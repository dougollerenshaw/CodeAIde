import sys
import os
import time


def log(message):
    log_path = os.path.expanduser("~/Desktop/codeaide_startup_log.txt")
    with open(log_path, "a") as f:
        f.write(f"{time.time()}: {message}\n")


log(f"Script started. Python version: {sys.version}")
log(f"Executable path: {sys.executable}")
log(f"Current working directory: {os.getcwd()}")


def main():
    log("Main function started")
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QLineEdit,
        QVBoxLayout,
        QWidget,
    )

    log("Modules imported")

    app = QApplication(sys.argv)
    log("QApplication created")

    class SimpleApp(QMainWindow):
        def __init__(self):
            super().__init__()
            log("SimpleApp init started")
            self.initUI()
            log("SimpleApp init completed")

        def initUI(self):
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            self.text_entry = QLineEdit(self)
            layout.addWidget(self.text_entry)

            self.setGeometry(300, 300, 300, 200)
            self.setWindowTitle("Simple CodeAide")

    ex = SimpleApp()
    log("SimpleApp instance created")
    ex.show()
    log("SimpleApp shown")
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Error in main: {str(e)}")
        raise
