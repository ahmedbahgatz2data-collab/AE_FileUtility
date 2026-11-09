import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

class FileUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Destination File Utility")
        self.root.geometry("650x550")
        self.root.minsize(600, 500)

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        # Variables
        self.list_path_var = tk.StringVar()
        self.action_choice = tk.IntVar(value=1)
        self.overwrite_choice = tk.IntVar(value=1)

        self.create_widgets()

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text=" 1. Select TXT Configuration File ", padding=10)
        file_frame.pack(fill=tk.X, pady=5)

        self.entry_path = ttk.Entry(file_frame, textvariable=self.list_path_var, width=50)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_browse = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Options Frame (Side by Side)
        options_container = ttk.Frame(main_frame)
        options_container.pack(fill=tk.X, pady=5)

        # 2. Action Choice
        action_frame = ttk.LabelFrame(options_container, text=" 2. Choose Action ", padding=10)
        action_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Radiobutton(action_frame, text="Copy files", variable=self.action_choice, value=1, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(action_frame, text="Move files", variable=self.action_choice, value=2, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(action_frame, text="Rename in-place only", variable=self.action_choice, value=3, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)

        # 3. Overwrite Mode
        self.overwrite_frame = ttk.LabelFrame(options_container, text=" 3. Overwrite Mode ", padding=10)
        self.overwrite_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.rb_ow_1 = ttk.Radiobutton(self.overwrite_frame, text="Overwrite existing", variable=self.overwrite_choice, value=1)
        self.rb_ow_1.pack(anchor=tk.W, pady=2)
        self.rb_ow_2 = ttk.Radiobutton(self.overwrite_frame, text="Auto-number duplicates", variable=self.overwrite_choice, value=2)
        self.rb_ow_2.pack(anchor=tk.W, pady=2)
        self.rb_ow_3 = ttk.Radiobutton(self.overwrite_frame, text="Skip existing", variable=self.overwrite_choice, value=3)
        self.rb_ow_3.pack(anchor=tk.W, pady=2)

        # Run Button
        self.btn_run = ttk.Button(main_frame, text="Start Operation", command=self.run_operation)
        self.btn_run.pack(fill=tk.X, pady=10)

        # Log Console Area
        log_frame = ttk.LabelFrame(main_frame, text=" Live Output & Logs ", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=12, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def toggle_overwrite_state(self):
        if self.action_choice.get() == 3:
            # Disable overwrite options for rename in-place
            self.rb_ow_1.config(state=tk.DISABLED)
            self.rb_ow_2.config(state=tk.DISABLED)
            self.rb_ow_3.config(state=tk.DISABLED)
        else:
            self.rb_ow_1.config(state=tk.NORMAL)
            self.rb_ow_2.config(state=tk.NORMAL)
            self.rb_ow_3.config(state=tk.NORMAL)

    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select TXT File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if filename:
            self.list_path_var.set(filename)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run_operation(self):
        list_path = self.list_path_var.get().strip()
        if not list_path or not os.path.exists(list_path):
            messagebox.showerror("Error", "Please select a valid TXT configuration file first!")
            return

        self.log_text.delete("1.0", tk.END)
        log_file_path = os.path.join(os.path.dirname(list_path), "transfer_log.txt")

        action = self.action_choice.get()
        overwrite_mode = self.overwrite_choice.get()

        self.log_message(f"=== Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        
        success_count = 0
        fail_count = 0

        try:
            with open(list_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            return

        for line in lines:
            parts = line.strip().split("\t")
            src_file = parts[0].strip() if len(parts) > 0 else ""
            dest_folder = parts[1].strip() if len(parts) > 1 else ""
            new_name = parts[2].strip() if len(parts) > 2 else ""

            if not src_file:
                continue

            if not os.path.exists(src_file):
                self.log_message(f"[NOT FOUND] {src_file}")
                fail_count += 1
                continue

            # ACTION 3: RENAME IN-PLACE
            if action == 3:
                if not new_name:
                    self.log_message(f"[SKIPPED] No new name provided: {src_file}")
                    continue
                
                src_folder, old_name = os.path.split(src_file)
                base_name, old_ext = os.path.splitext(old_name)
                
                # Check extension in new name
                if not os.path.splitext(new_name)[1]:
                    target_name = new_name + old_ext
                else:
                    target_name = new_name

                target_path = os.path.join(src_folder, target_name)

                if os.path.abspath(src_file).lower() == os.path.abspath(target_path).lower():
                    self.log_message(f"[SKIPPED] Name is identical: {src_file}")
                elif os.path.exists(target_path):
                    self.log_message(f"[ERROR] Target already exists: {target_path}")
                    fail_count += 1
                else:
                    try:
                        os.rename(src_file, target_path)
                        self.log_message(f"[RENAMED] {src_file} -> {target_name}")
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[ERROR] Failed to rename: {e}")
                        fail_count += 1

            # ACTIONS 1 & 2: COPY OR MOVE
            else:
                if not dest_folder:
                    self.log_message(f"[ERROR] No destination specified for: {src_file}")
                    fail_count += 1
                    continue

                if not os.path.exists(dest_folder):
                    try:
                        os.makedirs(dest_folder)
                    except Exception as e:
                        self.log_message(f"[ERROR] Could not create folder {dest_folder}: {e}")
                        fail_count += 1
                        continue

                orig_name = os.path.basename(src_file)
                final_filename = new_name if new_name else orig_name
                target_path = os.path.join(dest_folder, final_filename)

                should_process = True

                if os.path.exists(target_path):
                    if overwrite_mode == 3: # Skip
                        self.log_message(f"[SKIPPED] Already exists: {target_path}")
                        should_process = False
                    elif overwrite_mode == 2: # Auto-number
                        base_n, ext_n = os.path.splitext(final_filename)
                        count = 1
                        while True:
                            test_name = f"{base_n}_{count}{ext_n}"
                            test_path = os.path.join(dest_folder, test_name)
                            if not os.path.exists(test_path):
                                target_path = test_path
                                break
                            count += 1

                if should_process:
                    try:
                        if action == 2: # Move
                            shutil.move(src_file, target_path)
                            self.log_message(f"[MOVED] {src_file} -> {target_path}")
                        else: # Copy
                            shutil.copy2(src_file, target_path)
                            self.log_message(f"[COPIED] {src_file} -> {target_path}")
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[ERROR] Operation failed: {e}")
                        fail_count += 1

        self.log_message("\n========================================")
        self.log_message(f"Operation Complete! Successful: {success_count}, Failed/Skipped: {fail_count}")
        self.log_message("========================================")
        messagebox.showinfo("Done", f"Operation finished!\nSuccessful: {success_count}\nFailed/Skipped: {fail_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileUtilityApp(root)
    root.mainloop()
