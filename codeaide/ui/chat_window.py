import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from codeaide.ui.input_area import InputArea
from codeaide.ui.code_popup import CodePopup
from codeaide.utils import prompt_utils
from codeaide.utils.constants import (
    CHAT_WINDOW_WIDTH, CHAT_WINDOW_HEIGHT, CHAT_WINDOW_BG, CHAT_WINDOW_FG,
    USER_MESSAGE_COLOR, AI_MESSAGE_COLOR, USER_FONT, AI_FONT, AI_EMOJI
)

class ChatWindow:
    def __init__(self, chat_handler):
        self.root = tk.Tk()
        self.root.title("CodeAIde")
        self.root.geometry(f"{CHAT_WINDOW_WIDTH}x{CHAT_WINDOW_HEIGHT}")
        self.chat_handler = chat_handler
        self.cost_tracker = chat_handler.cost_tracker
        self.setup_ui()
        self.add_to_chat("AI", "I'm a code writing assistant. I can generate and run code for you. What would you like to do?")

    def setup_ui(self):
        self.chat_frame = ttk.Frame(self.root, padding="10")
        self.chat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            bg=CHAT_WINDOW_BG,
            fg=CHAT_WINDOW_FG,
            insertbackground=CHAT_WINDOW_FG
        )
        self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.chat_display.config(state=tk.DISABLED)

        # Create tags for different message styles
        self.chat_display.tag_config('user', foreground=USER_MESSAGE_COLOR, font=USER_FONT)
        self.chat_display.tag_config('ai', foreground=AI_MESSAGE_COLOR, font=AI_FONT)

        self.input_area = InputArea(
            self.chat_frame, 
            self.on_submit, 
            bg=CHAT_WINDOW_BG, 
            fg=USER_MESSAGE_COLOR, 
            font=USER_FONT
        )
        self.input_area.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Create a frame for buttons
        button_frame = ttk.Frame(self.chat_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Add buttons to the button frame
        self.submit_button = ttk.Button(button_frame, text="Submit", command=self.on_submit)
        self.submit_button.grid(row=0, column=0, padx=(0, 5))

        self.example_button = ttk.Button(button_frame, text="Use Example", command=self.load_example)
        self.example_button.grid(row=0, column=1, padx=(0, 5))

        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.on_exit)
        self.exit_button.grid(row=0, column=2)

        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

    def add_to_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        if sender == "User":
            self.chat_display.insert(tk.END, f"User: ", 'user')
            self.chat_display.insert(tk.END, f"{message}\n\n", 'user')
        else:
            self.chat_display.insert(tk.END, f"{AI_EMOJI}: ", 'ai')
            self.chat_display.insert(tk.END, f"{message}\n\n", 'ai')
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def on_submit(self, user_input=None):
        if user_input is None:
            user_input = self.input_area.get_input()
        if user_input:
            self.input_area.clear_input()
            self.add_to_chat("User", user_input)
            self.display_thinking()
            self.disable_ui_elements()
            self.root.after(100, self.process_input, user_input)

    def display_thinking(self):
        self.add_to_chat("AI", "Thinking... 🤔")

    def process_input(self, user_input):
        response = self.chat_handler.process_input(user_input)
        self.root.after(100, self.handle_response, response)

    def handle_response(self, response):
        # Remove all "Thinking..." messages
        self.remove_thinking_messages()

        # Re-enable UI elements
        self.enable_ui_elements()

        # Handle the response based on its type
        if response['type'] == 'message':
            self.add_to_chat("AI", response['message'])
        elif response['type'] == 'questions':
            message = response['message']
            questions = response['questions']
            combined_message = f"{message}\n" + "\n".join(f"  * {question}" for question in questions)
            self.add_to_chat("AI", combined_message)
            if self.chat_handler.is_task_in_progress():
                self.add_to_chat("AI", "Please provide answers to these questions to continue.")
        elif response['type'] == 'code':
            self.add_to_chat("AI", response['message'] + " Opening or updating code in the code window...")
            self.update_or_create_code_popup(response)
        elif response['type'] == 'error':
            self.add_to_chat("AI", response['message'])

    def remove_thinking_messages(self):
        self.chat_display.config(state=tk.NORMAL)
        end_index = self.chat_display.index(tk.END)
        line_count = int(end_index.split('.')[0])
        i = 1
        while i < line_count:
            line_start = f"{i}.0"
            line_end = f"{i}.end"
            line = self.chat_display.get(line_start, line_end)
            if "Thinking... 🤔" in line:
                next_line_start = f"{i+1}.0"
                next_line_end = f"{i+1}.end"
                next_line = self.chat_display.get(next_line_start, next_line_end)
                if next_line.strip() == "":
                    # Remove the "Thinking..." line and the following empty line
                    self.chat_display.delete(line_start, f"{i+2}.0")
                    line_count -= 2  # Adjust line count
                else:
                    # Remove only the "Thinking..." line
                    self.chat_display.delete(line_start, next_line_start)
                    line_count -= 1  # Adjust line count
            else:
                i += 1
        self.chat_display.config(state=tk.DISABLED)

    def disable_ui_elements(self):
        self.input_area.input_text.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)
        self.example_button.config(state=tk.DISABLED)

    def enable_ui_elements(self):
        self.input_area.input_text.config(state=tk.NORMAL)
        self.submit_button.config(state=tk.NORMAL)
        self.example_button.config(state=tk.NORMAL)

    def update_or_create_code_popup(self, response):
        if hasattr(self, 'code_popup') and self.code_popup and self.code_popup.top.winfo_exists():
            self.code_popup.update_with_new_version(response['code'], response.get('requirements', []))
        else:
            self.code_popup = CodePopup(self.root, self.chat_handler.file_handler, response['code'], response.get('requirements', []), self.chat_handler.run_generated_code)

    def load_example(self):
        example = prompt_utils.load_example_prompt('decaying_exponential_plot')
        if example:
            self.input_area.set_input(example)
        else:
            messagebox.showinfo("No Examples", "No example prompts are available.")

    def on_exit(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()

    def run(self):
        self.root.after(100, lambda: self.input_area.focus())
        self.root.mainloop()
        self.cost_tracker.print_summary()