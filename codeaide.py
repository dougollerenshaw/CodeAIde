import sys
from codeaide.ui.chat_window import ChatWindow
from codeaide.utils.api_utils import test_api_connection

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        success, message = test_api_connection()
        if success:
            print("Connection successful!")
            print("Claude says:", message)
        else:
            print("Connection failed.")
            print("Error:", message)
    else:
        app = ChatWindow()
        app.run()

if __name__ == "__main__":
    main()