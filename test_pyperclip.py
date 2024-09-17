import time
import pyperclip

last_value = pyperclip.paste()
while True:
    tmp_value = pyperclip.paste()
    if tmp_value != last_value:
        print("Clipboard changed:")
        print(repr(tmp_value))
        last_value = tmp_value
    time.sleep(0.1)