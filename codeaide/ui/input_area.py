import tkinter as tk
from tkinter import ttk

class InputArea(ttk.Frame):
    def __init__(self, parent, submit_callback, bg='white', fg='black'):
        super().__init__(parent)
        self.submit_callback = submit_callback
        self.bg = bg
        self.fg = fg
        self.setup_ui()

    def setup_ui(self):
        self.columnconfigure(0, weight=1)

        self.input_text = tk.Text(
            self, 
            wrap=tk.WORD, 
            width=70, 
            height=5,
            bg=self.bg,
            fg=self.fg,
            insertbackground=self.fg
        )
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E))

        input_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.input_text.yview)
        input_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.input_text.configure(yscrollcommand=input_scrollbar.set)

        self.input_text.bind('<Return>', self.on_return)
        self.input_text.bind('<Shift-Return>', self.on_shift_return)
        self.input_text.bind('<<Modified>>', self.on_modify)

    def on_return(self, event):
        self.submit_callback()
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