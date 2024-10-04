import sys
from unittest.mock import Mock, patch, MagicMock
import pytest
import logging
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer

from codeaide.ui.chat_window import ChatWindow
from codeaide.logic.chat_handler import ChatHandler
from codeaide.utils import general_utils
from codeaide.utils.constants import (
    AI_PROVIDERS,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
    MODEL_SWITCH_MESSAGE,
)

# Skip all tests in this file if running in CI
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true", reason="Running in CI environment"
)

# This is required for Qt tests
app = QApplication([])


@pytest.fixture
def mock_chat_handler():
    mock_handler = Mock(spec=ChatHandler)
    mock_handler.process_input = Mock(
        return_value={"type": "message", "message": "AI response"}
    )
    mock_handler.file_handler = Mock()
    mock_handler.file_handler.get_versions_dict = Mock(return_value={})
    mock_handler.get_latest_version = Mock(return_value="1.0")
    mock_handler.terminal_manager = Mock()

    # Add these new attributes
    mock_handler.api_key_valid = True
    mock_handler.api_key_message = "API key is valid"
    mock_handler.cost_tracker = Mock()

    # Mock the set_model method to return a tuple
    mock_handler.set_model = Mock(return_value=(True, "Model set successfully"))

    return mock_handler


@pytest.fixture
def chat_window(mock_chat_handler):
    def _create_window(api_key_valid=True):
        mock_chat_handler.api_key_valid = api_key_valid
        window = ChatWindow(mock_chat_handler)
        # Ensure that QTimer.singleShot calls are executed immediately
        QTimer.singleShot = lambda ms, callback: callback()
        return window

    return _create_window


def test_chat_window_initialization(chat_window):
    window = chat_window()  # Creates a window with a valid API key
    assert window.windowTitle() == "🤖 CodeAIde 🤖"
    assert window.chat_handler is not None


def test_send_message(chat_window, mock_chat_handler):
    window = chat_window()  # Create the window
    # Simulate typing a message
    QTest.keyClicks(window.input_text, "Hello, AI!")
    # Simulate pressing the submit button
    QTest.mouseClick(window.submit_button, Qt.LeftButton)
    # Check if the chat_handler's process_input method was called
    mock_chat_handler.process_input.assert_called_once_with("Hello, AI!")


def test_model_switching(chat_window, mock_chat_handler, caplog):
    caplog.set_level(logging.INFO)
    window = chat_window()

    test_provider = next(
        provider for provider in AI_PROVIDERS.keys() if provider != DEFAULT_PROVIDER
    )
    test_model = next(
        model
        for model in AI_PROVIDERS[test_provider]["models"].keys()
        if model != DEFAULT_MODEL
    )

    window.provider_dropdown.setCurrentText(test_provider)
    window.model_dropdown.setCurrentText(test_model)

    window.update_chat_handler()

    # Log important information
    logging.info(f"Final provider: {window.provider_dropdown.currentText()}")
    logging.info(f"Final model: {window.model_dropdown.currentText()}")

    # Check if the chat_handler's set_model method was called with the correct arguments
    mock_chat_handler.set_model.assert_called_with(test_provider, test_model)

    # Check if the correct message was added to the chat
    expected_message = MODEL_SWITCH_MESSAGE.format(
        provider=test_provider, model=test_model
    )
    assert expected_message in window.chat_display.toPlainText()

    # Assert that the important information was logged
    assert f"Final provider: {test_provider}" in caplog.text
    assert f"Final model: {test_model}" in caplog.text


@patch("codeaide.ui.chat_window.CodePopup")
def test_handle_code_response(mock_code_popup, chat_window, mock_chat_handler):
    window = chat_window()  # Create the window
    response = {
        "type": "code",
        "message": "Here's your code",
        "code": "print('Hello, World!')",
        "requirements": [],
    }

    window.handle_response(response)

    # Check if CodePopup was created with the correct arguments
    mock_code_popup.assert_called_once_with(
        window,
        mock_chat_handler.file_handler,
        mock_chat_handler.terminal_manager,
        "print('Hello, World!')",
        [],
        mock_chat_handler.run_generated_code,
        chat_handler=mock_chat_handler,
    )

    # Check if the message was added to the chat display
    assert "Here's your code" in window.chat_display.toPlainText()


def test_load_example(chat_window, monkeypatch):
    window = chat_window()  # Create the window
    # Mock the show_example_dialog function
    monkeypatch.setattr(
        "codeaide.ui.chat_window.show_example_dialog", lambda _: "Example code"
    )

    # Simulate clicking the load example button
    QTest.mouseClick(window.example_button, Qt.LeftButton)

    # Check if the example was loaded into the input text
    assert window.input_text.toPlainText() == "Example code"
