from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QComboBox, QPushButton, QLabel, QFileDialog, QApplication)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont
from codeaide.utils.constants import CODE_WINDOW_WIDTH, CODE_WINDOW_HEIGHT, CODE_WINDOW_BG, CODE_WINDOW_FG, CODE_FONT
from codeaide.utils import general_utils
import os

class CodePopup(QWidget):
    def __init__(self, parent, file_handler, code, requirements, run_callback):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("💻 Generated Code 💻")
        self.resize(CODE_WINDOW_WIDTH, CODE_WINDOW_HEIGHT)
        self.file_handler = file_handler
        self.run_callback = run_callback
        self.setup_ui()
        self.load_versions()
        self.show_code(code, requirements)
        self.position_window()
        self.loading_versions = False # Prevents multiple calls to on_version_change method
        self.show()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)  # Space between main components
        layout.setContentsMargins(8, 8, 8, 8)  # Margins around the entire window

        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet(f"""
            background-color: {CODE_WINDOW_BG};
            color: {CODE_WINDOW_FG};
            border: 1px solid #ccc;
            padding: 5px;
        """)
        self.text_area.setFont(general_utils.set_font(CODE_FONT))
        layout.addWidget(self.text_area)

        controls_layout = QVBoxLayout()
        
        version_label = QLabel("Choose a version to display/run:")
        controls_layout.addWidget(version_label)

        self.version_dropdown = QComboBox(self)
        self.version_dropdown.currentIndexChanged.connect(self.on_version_change)
        controls_layout.addWidget(self.version_dropdown)

        button_layout = QHBoxLayout()
        buttons = [
            ("Run Code", self.on_run),
            ("Copy Code", self.on_copy_code),
            ("Save Code", self.on_save_code),
            ("Copy Requirements", self.on_copy_requirements),
            ("Close", self.close)
        ]

        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            button_layout.addWidget(button)

        controls_layout.addLayout(button_layout)
        layout.addLayout(controls_layout)

    def bring_to_front(self):
        self.raise_()
        self.activateWindow()

    def update_with_new_version(self, code, requirements):
        self.load_versions()
        self.show_code(code, requirements)

    def load_versions(self):
        self.loading_versions = True  # Set flag before loading to prevent on_version_change from running
        self.versions_dict = self.file_handler.get_versions_dict()
        version_values = [f"v{version}: {data['version_description']}" 
                          for version, data in self.versions_dict.items()]
        self.version_dropdown.clear()
        self.version_dropdown.addItems(version_values)
        if version_values:
            self.version_dropdown.setCurrentIndex(len(version_values) - 1)
        self.loading_versions = False  # Reset flag after loading to allow on_version_change to run

    def show_code(self, code, requirements):
        self.text_area.setPlainText(code)
        self.current_requirements = requirements
        self.bring_to_front()

    def on_version_change(self):
        if self.loading_versions:
            return  # Exit early if we're still loading versions
        
        selected = self.version_dropdown.currentText()
        version = selected.split(':')[0].strip('v')
        version_data = self.versions_dict[version]
        code_path = version_data['code_path']
        with open(code_path, 'r') as file:
            code = file.read()
        requirements = version_data['requirements']
        self.show_code(code, requirements)

    def on_run(self):
        selected = self.version_dropdown.currentText()
        version = selected.split(':')[0].strip('v')
        version_data = self.versions_dict[version]
        code_path = version_data['code_path']
        requirements = version_data['requirements']
        
        req_file_name = f"requirements_{version}.txt"
        req_path = os.path.join(os.path.dirname(code_path), req_file_name)
        with open(req_path, 'w') as f:
            f.write('\n'.join(requirements))

        self.run_callback(code_path, req_path)

    def on_copy_code(self):
        QApplication.clipboard().setText(self.text_area.toPlainText())

    def on_save_code(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Code", "", "Python Files (*.py)")
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.toPlainText())

    def on_copy_requirements(self):
        QApplication.clipboard().setText("\n".join(self.current_requirements))

    def position_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width(), 0)
