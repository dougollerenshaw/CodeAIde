from PyQt5.QtWidgets import QMessageBox, QTextEdit
from PyQt5.QtGui import QFont
import logging


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger


class TracebackDialog(QMessageBox):
    def __init__(self, parent, traceback_text):
        super().__init__(parent)
        self.logger = get_logger()
        self.logger.info(
            f"TracebackDialog: Initializing with text: {traceback_text[:50]}..."
        )
        self.setWindowTitle("Error Detected")
        self.setText("An error was detected in the running script:")
        self.setInformativeText(traceback_text)
        self.setIcon(QMessageBox.Warning)

        self.setFixedWidth(600)
        self.setSizeGripEnabled(True)

        self.send_button = self.addButton("Request a fix", QMessageBox.ActionRole)
        self.ignore_button = self.addButton("Ignore", QMessageBox.RejectRole)

        text_browser = self.findChild(QTextEdit)
        if text_browser:
            font = QFont("Courier")
            font.setStyleHint(QFont.Monospace)
            font.setFixedPitch(True)
            font.setPointSize(10)
            text_browser.setFont(font)

    def exec_(self):
        self.logger.info("TracebackDialog: Executing dialog")
        super().exec_()
        user_choice = "fix" if self.clickedButton() == self.send_button else "ignore"
        self.logger.info(f"TracebackDialog: User chose to {user_choice} the traceback")
        return self.clickedButton() == self.send_button
