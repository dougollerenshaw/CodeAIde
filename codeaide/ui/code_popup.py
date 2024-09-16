import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from codeaide.utils.constants import MAX_CODE_WINDOW_HEIGHT
import os

class CodePopup:
    def __init__(self, parent, file_handler, code, requirements, run_callback):
        self.top = tk.Toplevel(parent)
        self.top.title("Generated Code")
        self.file_handler = file_handler
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
        self.text_area.config(state=tk.DISABLED)

        controls_frame = ttk.Frame(self.top)
        controls_frame.pack(pady=10, fill=tk.X)

        # Add title for version dropdown
        version_title = ttk.Label(controls_frame, text="Choose a version to display/run:")
        version_title.pack(side=tk.TOP, anchor=tk.W, padx=5, pady=(0, 5))

        self.version_var = tk.StringVar()
        self.version_dropdown = ttk.Combobox(controls_frame, textvariable=self.version_var, width=60)
        self.version_dropdown.pack(side=tk.TOP, padx=5, fill=tk.X, expand=True)
        self.version_dropdown.bind("<<ComboboxSelected>>", self.on_version_change)

        # Configure the dropdown to allow text wrapping
        style = ttk.Style()
        style.configure('TCombobox', wrapLength=500)  # Adjust wrapLength as needed

        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(side=tk.TOP, pady=(10, 0), fill=tk.X)

        buttons = [
            ("Run Code", self.on_run),
            ("Copy Code", self.on_copy_code),
            ("Save Code", self.on_save_code),
            ("Copy Requirements", self.on_copy_requirements),
            ("Close", self.top.destroy)
        ]

        for text, command in buttons:
            button = ttk.Button(button_frame, text=text, command=command)
            button.pack(side=tk.LEFT, padx=5)

    def bring_to_front(self):
        self.top.lift()
        self.top.attributes('-topmost', True)
        self.top.after_idle(self.top.attributes, '-topmost', False)

    def update_with_new_version(self, code, requirements):
        self.load_versions()
        self.show_code(code, requirements)

    def load_versions(self):
        self.versions_dict = self.file_handler.get_versions_dict()
        version_values = [f"v{version}: {data['version_description']}" 
                        for version, data in self.versions_dict.items()]
        self.version_dropdown['values'] = version_values
        if version_values:
            self.version_var.set(version_values[-1])
            self.on_version_change(None)

    def show_code(self, code, requirements):
        self.text_area.config(state=tk.NORMAL)  # Temporarily enable editing
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert(tk.INSERT, code)
        self.text_area.config(state=tk.DISABLED)  # Disable editing again
        self.current_requirements = requirements
        self.bring_to_front()

    def on_version_change(self, event):
        selected = self.version_var.get()
        version = selected.split(':')[0].strip('v')
        version_data = self.versions_dict[version]
        code_path = version_data['code_path']
        with open(code_path, 'r') as file:
            code = file.read()
        requirements = version_data['requirements']
        self.show_code(code, requirements)
        self.bring_to_front()

    def on_run(self):
        selected = self.version_var.get()
        version = selected.split(':')[0].strip('v')
        version_data = self.versions_dict[version]
        code_path = version_data['code_path']
        requirements = version_data['requirements']
        
        # Create a requirements file
        req_file_name = f"requirements_{version}.txt"
        req_path = os.path.join(os.path.dirname(code_path), req_file_name)
        with open(req_path, 'w') as f:
            f.write('\n'.join(requirements))

        self.run_callback(code_path, req_path)

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
        self.bring_to_front()