from PyQt5.QtWidgets import QSplashScreen, QProgressBar
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__()

        # Create a pixmap for the splash screen (you can replace this with your own image)
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.white)
        self.setPixmap(pixmap)

        # Add a progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(10, 150, 380, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Add some text
        self.setStyleSheet("QSplashScreen { color: black; font-size: 14px; }")
        self.showMessage(
            "Loading CodeAIde...", Qt.AlignCenter | Qt.AlignBottom, Qt.black
        )

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.showMessage(message, Qt.AlignCenter | Qt.AlignBottom, Qt.black)
