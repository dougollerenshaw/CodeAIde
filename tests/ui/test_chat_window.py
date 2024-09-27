import sys
from unittest.mock import Mock, patch, MagicMock
import pytest
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
    mock_handler.cost_tracker = Mock()
    mock_handler.api_key_valid = True
    mock_handler.api_key_message = "API key is valid"
    mock_handler.file_handler = Mock()
    mock_handler.process_input = Mock(
        return_value={"type": "message", "message": "AI response"}
    )
    mock_handler.set_model = Mock(return_value=(True, "Model set successfully"))
    mock_handler.get_latest_version = Mock(
        return_value="1.0"
    )  # Ensure this returns a string
    return mock_handler


@pytest.fixture
def chat_window(mock_chat_handler):
    window = ChatWindow(mock_chat_handler)
    # Ensure that QTimer.singleShot calls are executed immediately
    QTimer.singleShot = lambda ms, callback: callback()
    return window


def test_chat_window_initialization(chat_window):
    assert chat_window.windowTitle() == "🤖 CodeAIde 🤖"
    assert chat_window.chat_handler is not None


def test_send_message(chat_window, mock_chat_handler):
    # Simulate typing a message
    QTest.keyClicks(chat_window.input_text, "Hello, AI!")

    # Simulate pressing the submit button
    QTest.mouseClick(chat_window.submit_button, Qt.LeftButton)

    # Check if the chat_handler's process_input method was called
    mock_chat_handler.process_input.assert_called_once_with("Hello, AI!")


def test_model_switching(chat_window, mock_chat_handler):
    print("Initial provider:", chat_window.provider_dropdown.currentText())
    print("Initial model:", chat_window.model_dropdown.currentText())

    # Get a non-default provider
    test_provider = next(
        provider for provider in AI_PROVIDERS.keys() if provider != DEFAULT_PROVIDER
    )

    # Change to the test provider
    chat_window.provider_dropdown.setCurrentText(test_provider)
    print(f"Provider after change: {chat_window.provider_dropdown.currentText()}")
    print(f"Model after provider change: {chat_window.model_dropdown.currentText()}")

    # Print all available models for the test provider
    print(f"Available models for {test_provider}:")
    for model in AI_PROVIDERS[test_provider]["models"].keys():
        print(model)

    # Select a non-default model for the test provider
    test_model = next(
        model
        for model in AI_PROVIDERS[test_provider]["models"].keys()
        if model != DEFAULT_MODEL
    )
    chat_window.model_dropdown.setCurrentText(test_model)
    print(
        f"Provider after model selection: {chat_window.provider_dropdown.currentText()}"
    )
    print(f"Model after model selection: {chat_window.model_dropdown.currentText()}")

    # Manually trigger the update_chat_handler method
    chat_window.update_chat_handler()

    print("All calls to set_model:")
    for call in mock_chat_handler.set_model.call_args_list:
        print(call)

    print(f"Final provider: {chat_window.provider_dropdown.currentText()}")
    print(f"Final model: {chat_window.model_dropdown.currentText()}")

    # Check if the chat_handler's set_model method was called with the correct arguments
    mock_chat_handler.set_model.assert_any_call(test_provider, test_model)

    print("Chat display content:")
    print(chat_window.chat_display.toPlainText())

    # Check if the correct message was added to the chat
    current_version = "1.0"  # This should match what's set in the mock_chat_handler
    new_version = general_utils.increment_version(
        current_version, major_or_minor="major", increment=1
    )
    expected_message = MODEL_SWITCH_MESSAGE.format(
        provider=test_provider,
        model=test_model,
        current_version=current_version,
        new_version=new_version,
    )
    assert expected_message in chat_window.chat_display.toPlainText()


@patch("codeaide.ui.chat_window.CodePopup")
def test_handle_code_response(mock_code_popup, chat_window, mock_chat_handler):
    response = {
        "type": "code",
        "message": "Here's your code",
        "code": "print('Hello, World!')",
        "requirements": [],
    }

    chat_window.handle_response(response)

    # Check if CodePopup was created
    mock_code_popup.assert_called_once()

    # Check if the message was added to the chat display
    assert "Here's your code" in chat_window.chat_display.toPlainText()


def test_load_example(chat_window, monkeypatch):
    # Mock the show_example_dialog function
    monkeypatch.setattr(
        "codeaide.ui.chat_window.show_example_dialog", lambda _: "Example code"
    )

    # Simulate clicking the load example button
    QTest.mouseClick(chat_window.example_button, Qt.LeftButton)

    # Check if the example was loaded into the input text
    assert chat_window.input_text.toPlainText() == "Example code"
