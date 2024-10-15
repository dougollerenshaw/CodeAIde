import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt, QSharedMemory
from codeaide.logic.chat_handler import ChatHandler
from codeaide.utils import api_utils
from codeaide.ui.splash_screen import SplashScreen
from codeaide.ui.chat_window import ChatWindow
import traceback


def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg, file=sys.stderr)
    sys.stderr.flush()
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setText("An unexpected error occurred.")
    msg_box.setInformativeText(str(value))
    msg_box.setDetailedText(error_msg)
    msg_box.setWindowTitle("Error")
    msg_box.exec_()


def main():
    # Create QApplication instance
    app = QApplication(sys.argv)

    # Check for existing instance
    shared_memory = QSharedMemory("CodeAideUniqueKey")
    if shared_memory.attach():
        print("Application is already running.")
        sys.exit(1)

    if not shared_memory.create(1):
        print("Failed to create shared memory.")
        sys.exit(1)

    sys.excepthook = exception_hook

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Show the splash screen immediately
    splash = SplashScreen()
    splash.show()
    app.processEvents()  # This ensures the splash screen is displayed immediately

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success, message = api_utils.check_api_connection()
        if success:
            print("Connection successful!")
            print("Claude says:", message)
        else:
            print("Connection failed.")
            print("Error:", message)
        sys.exit(0)  # Exit after test
    else:
        # Function to update progress
        def update_progress(value, message):
            splash.update_progress(value, message)
            app.processEvents()  # Ensure UI updates

        # Create ChatHandler (this might take some time)
        update_progress(10, "Initializing ChatHandler...")
        chat_handler = ChatHandler()

        # Create main window
        update_progress(50, "Creating main window...")
        main_window = ChatWindow(chat_handler)

        # Function to finish startup
        def finish_startup():
            main_window.show()
            splash.finish(main_window)

        # Use a timer to allow the splash screen to update
        QTimer.singleShot(100, finish_startup)

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
