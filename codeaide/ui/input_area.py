import tkinter as tk
from tkinter import ttk, TclError

class InputArea(ttk.Frame):
    def __init__(self, parent, submit_callback, bg='white', fg='black', font=None):
        super().__init__(parent)
        self.submit_callback = submit_callback
        self.bg = bg
        self.fg = fg
        self.font = font
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)

        self.input_text = tk.Text(
            self, 
            wrap=tk.WORD, 
            height=5,
            bg=self.bg,
            fg=self.fg,
            font=self.font,
            insertbackground=self.fg
        )
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        input_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.input_text.yview)
        input_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.input_text.configure(yscrollcommand=input_scrollbar.set)

        self.input_text.bind('<Return>', self.on_return)
        self.input_text.bind('<Shift-Return>', self.on_shift_return)
        self.input_text.bind('<<Modified>>', self.on_modify)
        self.input_text.bind('<Control-v>', self.custom_paste)

    def custom_paste(self, event=None):
        try:
            # Try to get clipboard contents as UTF8 string
            clipboard_content = self.clipboard_get()
        except TclError:
            try:
                # If UTF8 fails, try as a plain string
                clipboard_content = self.clipboard_get(type='STRING')
            except TclError:
                # If both fail, inform the user
                print("Unable to paste. Clipboard content is not text.")
                return "break"
        
        # Insert the clipboard content
        self.input_text.insert(tk.INSERT, clipboard_content)
        return "break"  # Prevents the default paste behavior

    def on_return(self, event):
        user_input = self.get_input()
        self.clear_input()
        self.submit_callback(user_input)
        return 'break'

    def on_shift_return(self, event):
        self.input_text.insert(tk.INSERT, '\n')
        return 'break'

    def on_modify(self, event):
        self.input_text.see(tk.END)
        self.input_text.edit_modified(False)

    def get_input(self):
        return self.input_text.get("1.0", tk.END).strip()

    def set_input(self, text):
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, text)
        self.input_text.see(tk.END)

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)

    def focus(self):
        self.input_text.focus_set()