import sys
from PyQt5.QtWidgets import QApplication
from codeaide.logic.chat_handler import ChatHandler
from codeaide.ui.chat_window import ChatWindow

def main():
    chat_handler = ChatHandler()

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success, message = chat_handler.check_api_connection()
        if success:
            print("Connection successful!")
            print("Claude says:", message)
        else:
            print("Connection failed.")
            print("Error:", message)
    else:
        app = QApplication(sys.argv)
        chat_window = ChatWindow(chat_handler)
        chat_window.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()