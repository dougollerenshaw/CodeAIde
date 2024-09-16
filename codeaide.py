import sys
from codeaide.logic.chat_handler import ChatHandler
from codeaide.ui.chat_window import ChatWindow

def main():
    chat_handler = ChatHandler()

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success, message = chat_handler.test_api_connection()
        if success:
            print("Connection successful!")
            print("Claude says:", message)
        else:
            print("Connection failed.")
            print("Error:", message)
    else:
        app = ChatWindow(chat_handler)
        app.run()

if __name__ == "__main__":
    main()