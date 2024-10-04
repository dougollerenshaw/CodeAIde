from PyQt5.QtWidgets import QMessageBox, QTextEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class TracebackDialog(QMessageBox):
    def __init__(self, parent, traceback_text):
        super().__init__(parent)
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
        super().exec_()
        return self.clickedButton() == self.send_button
