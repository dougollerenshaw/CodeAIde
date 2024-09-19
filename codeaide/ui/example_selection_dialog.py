from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QListWidget,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
)

from codeaide.utils import general_utils
from codeaide.utils.constants import CHAT_WINDOW_BG, CHAT_WINDOW_FG


class ExampleSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select an Example")
        self.setGeometry(100, 100, 600, 600)
        self.setModal(True)
        self.layout = QVBoxLayout()

        self.layout.setSpacing(5)
        self.layout.setContentsMargins(8, 8, 8, 8)

        # Create a splitter to divide the list and preview
        self.splitter = QSplitter(Qt.Vertical)

        self.example_list = QListWidget()
        self.preview_text = QTextBrowser()

        self.splitter.addWidget(self.example_list)
        self.splitter.addWidget(self.preview_text)

        # Set the ratio to 1:3 (20% list, 80% preview)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)

        self.layout.addWidget(self.splitter)
        self.select_button = QPushButton("Select")
        self.layout.addWidget(self.select_button)
        self.setLayout(self.layout)

        self.examples = general_utils.load_examples()
        self.load_examples()
        self.select_button.clicked.connect(self.accept)
        self.example_list.currentItemChanged.connect(self.update_preview)

        # Select the first item by default
        if self.example_list.count() > 0:
            self.example_list.setCurrentRow(0)

    def load_examples(self):
        for example in self.examples:
            self.example_list.addItem(example["description"])

    def update_preview(self, current, previous):
        if current:
            for example in self.examples:
                if example["description"] == current.text():
                    self.preview_text.setPlainText(example["prompt"])
                    break

    def get_selected_example(self):
        selected_items = self.example_list.selectedItems()
        if selected_items:
            selected_description = selected_items[0].text()
            for example in self.examples:
                if example["description"] == selected_description:
                    return example["prompt"]
        return None


def show_example_dialog(parent):
    dialog = ExampleSelectionDialog(parent)
    if dialog.exec_():
        return dialog.get_selected_example()
    return None
