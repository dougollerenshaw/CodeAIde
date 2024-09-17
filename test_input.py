import tkinter as tk
from tkinter import ttk
import pyperclip

class SimpleInputTest:
    def __init__(self, master):
        self.master = master
        master.title("Custom Paste Input Test")

        self.text_input = tk.Text(master, height=10, width=50)
        self.text_input.pack(padx=10, pady=10)

        self.paste_button = ttk.Button(master, text="Custom Paste", command=self.custom_paste)
        self.paste_button.pack(pady=5)

        self.print_button = ttk.Button(master, text="Print Content", command=self.print_content)
        self.print_button.pack(pady=5)

    def custom_paste(self):
        clipboard_content = pyperclip.paste()
        self.text_input.insert(tk.INSERT, clipboard_content)

    def print_content(self):
        content = self.text_input.get("1.0", tk.END)
        print("Text content:", repr(content))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleInputTest(root)
    root.mainloop()