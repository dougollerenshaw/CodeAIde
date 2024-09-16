import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from codeaide.utils.constants import MAX_CODE_WINDOW_HEIGHT
from codeaide.utils.file_handler import FileHandler

class CodePopup:
    def __init__(self, parent, code, requirements, run_callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Generated Code")
        self.file_handler = FileHandler()
        self.run_callback = run_callback
        self.setup_ui()
        self.load_versions()
        self.show_code(code, requirements)
        self.top.update_idletasks()
        self.position_window()

    def setup_ui(self):
        self.text_area = scrolledtext.ScrolledText(
            self.top, 
            wrap=tk.NONE,
            width=80, 
            height=MAX_CODE_WINDOW_HEIGHT,
            bg='black',
            fg='white',
            insertbackground='white'
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)  # This line disables editing

        controls_frame = ttk.Frame(self.top)
        controls_frame.pack(pady=10, fill=tk.X)

        self.version_var = tk.StringVar()
        self.version_dropdown = ttk.Combobox(controls_frame, textvariable=self.version_var)
        self.version_dropdown.pack(side=tk.LEFT, padx=5)
        self.version_dropdown.bind("<<ComboboxSelected>>", self.on_version_change)

        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side=tk.RIGHT)

        run_button = ttk.Button(button_frame, text="Run Code", command=self.on_run)
        run_button.pack(side=tk.LEFT, padx=5)

        copy_code_button = ttk.Button(button_frame, text="Copy Code", command=self.on_copy_code)
        copy_code_button.pack(side=tk.LEFT, padx=5)

        save_code_button = ttk.Button(button_frame, text="Save Code", command=self.on_save_code)
        save_code_button.pack(side=tk.LEFT, padx=5)

        copy_req_button = ttk.Button(button_frame, text="Copy Requirements", command=self.on_copy_requirements)
        copy_req_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(button_frame, text="Close", command=self.top.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

    def update_with_new_version(self, code, requirements):
        self.load_versions()
        self.show_code(code, requirements)

    def load_versions(self):
        versions = self.file_handler.get_versions()
        self.version_dropdown['values'] = versions
        if versions:
            latest_version = max(versions)
            self.version_var.set(latest_version)
            self.on_version_change(None)  # Update displayed code

    def show_code(self, code, requirements):
        self.text_area.config(state=tk.NORMAL)  # Temporarily enable editing
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.INSERT, code)
        self.text_area.config(state=tk.DISABLED)  # Disable editing again
        self.current_requirements = requirements

    def on_version_change(self, event):
        version = int(self.version_var.get())
        code = self.file_handler.get_code(version)
        requirements = self.file_handler.get_requirements(version)
        self.show_code(code, requirements)

    def on_run(self):
        version = int(self.version_var.get())
        self.run_callback(f"generated_script_{version}.py", f"requirements_{version}.txt")

    def on_copy_code(self):
        self.top.clipboard_clear()
        self.top.clipboard_append(self.text_area.get("1.0", tk.END))

    def on_save_code(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py")
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.get("1.0", tk.END))

    def on_copy_requirements(self):
        self.top.clipboard_clear()
        self.top.clipboard_append("\n".join(self.current_requirements))

    def position_window(self):
        screen_width = self.top.winfo_screenwidth()
        window_width = self.top.winfo_width()
        x = screen_width - window_width
        y = 0
        self.top.geometry(f"+{x}+{y}")