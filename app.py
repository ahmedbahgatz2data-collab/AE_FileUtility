import os
import json
import shutil
import sys
import threading
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timedelta

CONFIG_FILE = "AE_FileUtility_config.json"
CURRENT_VERSION = "1.1.0"
GITHUB_REPO = "ahmedbahgatz2data-collab/AE_FileUtility"

class FileUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"AE_FileUtility - Ultimate File Manager (v{CURRENT_VERSION})")
        self.root.geometry("750x730")
        self.root.minsize(680, 650)

        style = ttk.Style()
        style.theme_use("clam")

        self.bg_color = "#f4f6f9"
        self.primary_color = "#2563eb"
        self.primary_hover = "#1d4ed8"
        self.text_color = "#1f2937"
        self.border_color = "#d1d5db"

        self.root.configure(bg=self.bg_color)

        style.configure(".", font=("Segoe UI", 10), background=self.bg_color, foreground=self.text_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        style.configure("TLabelframe", background=self.bg_color, bordercolor=self.border_color, borderwidth=1)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), background=self.bg_color, foreground=self.primary_color)
        
        style.configure("TButton", font=("Segoe UI", 10), padding=6, relief="flat", background="#e5e7eb")
        style.map("TButton", background=[("active", "#d1d5db"), ("pressed", "#9ca3af")])

        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="#ffffff", padding=8)
        style.map("Primary.TButton", 
                  background=[("active", self.primary_hover), ("pressed", "#1e40af")],
                  foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])

        # Variables
        self.list_path_var = tk.StringVar()
        self.filter_ext_var = tk.StringVar(value="")
        self.filter_days_var = tk.StringVar(value="")  # فلترة الأيام الأخيرة
        self.action_choice = tk.IntVar(value=1)
        self.overwrite_choice = tk.IntVar(value=1)
        self.last_log_content = ""
        self.undo_stack = []

        self.load_settings()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.check_silent_updates, daemon=True).start()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        template_frame = ttk.LabelFrame(main_frame, text=" 📥 Quick Start Template ", padding=8)
        template_frame.pack(fill=tk.X, pady=(0, 8))

        lbl_tip = ttk.Label(template_frame, text="Download structured TXT template with instructions & examples.")
        lbl_tip.pack(side=tk.LEFT, padx=5)

        btn_download_template = ttk.Button(template_frame, text="Download Template", command=self.download_template)
        btn_download_template.pack(side=tk.RIGHT, padx=5)

        # 1. File Selection & Advanced Filters Section
        file_frame = ttk.LabelFrame(main_frame, text=" 📂 1. Configuration & Smart Filters ", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 8))

        f_top = ttk.Frame(file_frame)
        f_top.pack(fill=tk.X, pady=2)
        self.entry_path = ttk.Entry(f_top, textvariable=self.list_path_var, font=("Segoe UI", 10))
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        btn_browse = ttk.Button(f_top, text="Browse...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Filters Row
        f_bottom = ttk.Frame(file_frame)
        f_bottom.pack(fill=tk.X, pady=(8, 2))
        
        ttk.Label(f_bottom, text="Ext (e.g. .pdf):").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_filter_ext = ttk.Entry(f_bottom, textvariable=self.filter_ext_var, width=8)
        self.entry_filter_ext.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(f_bottom, text="Modified within last X days (e.g. 7):").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_filter_days = ttk.Entry(f_bottom, textvariable=self.filter_days_var, width=6)
        self.entry_filter_days.pack(side=tk.LEFT)

        options_container = ttk.Frame(main_frame)
        options_container.pack(fill=tk.X, pady=(0, 8))

        action_frame = ttk.LabelFrame(options_container, text=" ⚙️ 2. Choose Action ", padding=10)
        action_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Radiobutton(action_frame, text="Copy files", variable=self.action_choice, value=1, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(action_frame, text="Move files", variable=self.action_choice, value=2, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(action_frame, text="Rename in-place only", variable=self.action_choice, value=3, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=2)

        self.overwrite_frame = ttk.LabelFrame(options_container, text=" 🔄 3. Overwrite Mode ", padding=10)
        self.overwrite_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.rb_ow_1 = ttk.Radiobutton(self.overwrite_frame, text="Overwrite existing", variable=self.overwrite_choice, value=1)
        self.rb_ow_1.pack(anchor=tk.W, pady=2)
        self.rb_ow_2 = ttk.Radiobutton(self.overwrite_frame, text="Auto-number duplicates", variable=self.overwrite_choice, value=2)
        self.rb_ow_2.pack(anchor=tk.W, pady=2)
        self.rb_ow_3 = ttk.Radiobutton(self.overwrite_frame, text="Skip existing", variable=self.overwrite_choice, value=3)
        self.rb_ow_3.pack(anchor=tk.W, pady=2)

        self.btn_run = ttk.Button(main_frame, text="🚀 Start Operation", command=self.run_operation, style="Primary.TButton")
        self.btn_run.pack(fill=tk.X, pady=(0, 5))

        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 8))

        log_frame = ttk.LabelFrame(main_frame, text=" 💻 Live Output & Logs ", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=9, bg="#1e1e1e", fg="#4ec9b0", font=("Consolas", 9), bd=0, highlightthickness=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X)

        self.btn_undo = ttk.Button(bottom_bar, text="↩️ Undo Last Operation", command=self.undo_operation, state=tk.DISABLED)
        self.btn_undo.pack(side=tk.LEFT)

        self.btn_export_report = ttk.Button(bottom_bar, text="📊 Download Tab-Delimited Report", command=self.export_report, state=tk.DISABLED)
        self.btn_export_report.pack(side=tk.RIGHT)

    def check_silent_updates(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'AE_FileUtility-Updater'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").strip("v")
                
                if latest_version and latest_version != CURRENT_VERSION:
                    for asset in data.get("assets", []):
                        if asset["name"] == "AE_FileUtility.exe":
                            download_url = asset["browser_download_url"]
                            temp_path = os.path.join(os.environ.get("TEMP", "."), "AE_FileUtility_new.exe")
                            urllib.request.urlretrieve(download_url, temp_path)
                            
                            current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
                            if getattr(sys, 'frozen', False):
                                batch_path = os.path.join(os.environ.get("TEMP", "."), "update.bat")
                                with open(batch_path, "w", encoding="utf-8") as b_file:
                                    b_file.write(f"@echo off\n")
                                    b_file.write(f"timeout /t 2 /nobreak > nul\n")
                                    b_file.write(f"move /y \"{temp_path}\" \"{current_exe}\"\n")
                                    b_file.write(f"start \"\" \"{current_exe}\"\n")
                                    b_file.write(f"del \"%~f0\"\n")
                            break
        except Exception:
            pass

    def toggle_overwrite_state(self):
        if self.action_choice.get() == 3:
            self.rb_ow_1.config(state=tk.DISABLED)
            self.rb_ow_2.config(state=tk.DISABLED)
            self.rb_ow_3.config(state=tk.DISABLED)
        else:
            self.rb_ow_1.config(state=tk.NORMAL)
            self.rb_ow_2.config(state=tk.NORMAL)
            self.rb_ow_3.config(state=tk.NORMAL)

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.action_choice.set(data.get("action", 1))
                    self.overwrite_choice.set(data.get("overwrite", 1))
                    self.filter_ext_var.set(data.get("filter_ext", ""))
                    self.filter_days_var.set(data.get("filter_days", ""))
            except Exception:
                pass

    def save_settings(self):
        data = {
            "action": self.action_choice.get(),
            "overwrite": self.overwrite_choice.get(),
            "filter_ext": self.filter_ext_var.get(),
            "filter_days": self.filter_days_var.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def on_close(self):
        self.save_settings()
        batch_path = os.path.join(os.environ.get("TEMP", "."), "update.bat")
        if os.path.exists(batch_path):
            os.startfile(batch_path)
        self.root.destroy()

    def download_template(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="AE_FileUtility_template.txt",
            title="Save Template File"
        )
        if file_path:
            template_content = (
                "# === AE_FILEUTILITY CONFIGURATION TEMPLATE ===\n"
                "# Format: 3 Columns separated by TAB character.\n"
                "# Column 1: Source File Path (Required)\n"
                "# Column 2: Destination Folder (Required for Copy/Move, leave blank for In-place Rename)\n"
                "# Column 3: New File Name (Optional: leave blank to keep original name)\n"
                "# -------------------------------------------------------------------------\n"
                "C:\\Docs\\file.pdf\tD:\\Backup\tReport_2026.pdf\n"
                "C:\\Images\\photo.jpg\tE:\\Photos\t\n"
                "D:\\Work\\Data.xlsx\t\tData_V2.xlsx\n"
            )
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(template_content)
                messagebox.showinfo("Success", f"Template file saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save template: {e}")

    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select TXT File", filetypes=(("Text Files", "*.txt"), ("All Files", "*.*")))
        if filename:
            self.list_path_var.set(filename)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def export_report(self):
        if not self.last_log_content:
            messagebox.showwarning("Warning", "No logs to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="AE_FileUtility_report.txt",
            title="Save Tab-Delimited Report"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.last_log_content)
                messagebox.showinfo("Success", f"Tab-delimited report saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save report: {e}")

    def undo_operation(self):
        if not self.undo_stack:
            messagebox.showinfo("Undo", "No operations to undo.")
            return

        success_undo = 0
        self.log_message("\n--- STARTING UNDO PROCESS ---")
        
        while self.undo_stack:
            action_type, param1, param2 = self.undo_stack.pop()
            try:
                if action_type == "COPY":
                    if os.path.exists(param2):
                        os.remove(param2)
                        success_undo += 1
                elif action_type == "MOVE":
                    if os.path.exists(param2) and not os.path.exists(param1):
                        shutil.move(param2, param1)
                        success_undo += 1
                elif action_type == "RENAME":
                    if os.path.exists(param2) and not os.path.exists(param1):
                        os.rename(param2, param1)
                        success_undo += 1
            except Exception as e:
                self.log_message(f"[UNDO ERROR] Failed to revert {param2}: {e}")

        self.log_message(f"Undo Complete! Successfully reverted {success_undo} items.")
        messagebox.showinfo("Undo Finished", f"Successfully reverted {success_undo} actions.")
        self.btn_undo.config(state=tk.DISABLED)

    def run_operation(self):
        list_path = self.list_path_var.get().strip()
        if not list_path or not os.path.exists(list_path):
            messagebox.showerror("Error", "Please select a valid TXT configuration file first!")
            return

        self.save_settings()
        self.log_text.delete("1.0", tk.END)
        self.undo_stack.clear()
        
        report_rows = []
        action = self.action_choice.get()
        overwrite_mode = self.overwrite_choice.get()
        
        filter_ext = self.filter_ext_var.get().strip().lower()
        filter_days_str = self.filter_days_var.get().strip()
        
        max_days = None
        if filter_days_str.isdigit():
            max_days = int(filter_days_str)

        try:
            with open(list_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            return

        total_lines = len(lines)
        if total_lines == 0:
            messagebox.showwarning("Warning", "The configuration file is empty!")
            return

        self.progress["maximum"] = total_lines
        self.progress["value"] = 0

        start_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_message(f"AE_FileUtility Session Started: {start_time_str}")
        report_rows.append(f"Session Start\t{start_time_str}\t")
        report_rows.append("Status\tSource File\tDestination / Result")

        success_count = 0
        fail_count = 0

        for idx, line in enumerate(lines, start=1):
            self.progress["value"] = idx
            self.root.update_idletasks()

            parts = line.split("\t")
            src_file = parts[0].strip() if len(parts) > 0 else ""
            dest_folder = parts[1].strip() if len(parts) > 1 else ""
            new_name = parts[2].strip() if len(parts) > 2 else ""

            if not src_file:
                continue

            if not os.path.exists(src_file):
                self.log_message(f"[NOT FOUND] {src_file}")
                report_rows.append(f"NOT FOUND\t{src_file}\tFile does not exist")
                fail_count += 1
                continue

            # 1. Extension Filter Check
            if filter_ext:
                _, ext = os.path.splitext(src_file)
                if ext.lower() != filter_ext:
                    continue

            # 2. Date / Modified Time Filter Check
            if max_days is not None:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(src_file))
                time_threshold = datetime.now() - timedelta(days=max_days)
                if file_mtime < time_threshold:
                    # أقدم من الفترة المطلوبة، يتم تخطيه بصمت
                    continue

            if action == 3:
                if not new_name:
                    self.log_message(f"[SKIPPED] No new name provided: {src_file}")
                    report_rows.append(f"SKIPPED\t{src_file}\tNo new name provided")
                    continue
                
                src_folder, old_name = os.path.split(src_file)
                _, old_ext = os.path.splitext(old_name)
                target_name = new_name if os.path.splitext(new_name)[1] else new_name + old_ext
                target_path = os.path.join(src_folder, target_name)

                if os.path.abspath(src_file).lower() == os.path.abspath(target_path).lower():
                    self.log_message(f"[SKIPPED] Name is identical: {src_file}")
                elif os.path.exists(target_path):
                    self.log_message(f"[ERROR] Target already exists: {target_path}")
                    report_rows.append(f"ERROR\t{src_file}\tTarget already exists: {target_path}")
                    fail_count += 1
                else:
                    try:
                        os.rename(src_file, target_path)
                        self.undo_stack.append(("RENAME", src_file, target_path))
                        self.log_message(f"[RENAMED] {src_file} -> {target_name}")
                        report_rows.append(f"RENAMED\t{src_file}\t{target_path}")
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[ERROR] Failed to rename: {e}")
                        report_rows.append(f"ERROR\t{src_file}\tFailed to rename: {e}")
                        fail_count += 1
            else:
                if not dest_folder:
                    self.log_message(f"[ERROR] No destination specified for: {src_file}")
                    report_rows.append(f"ERROR\t{src_file}\tNo destination specified")
                    fail_count += 1
                    continue

                if not os.path.exists(dest_folder):
                    try:
                        os.makedirs(dest_folder)
                    except Exception as e:
                        self.log_message(f"[ERROR] Could not create folder: {e}")
                        report_rows.append(f"ERROR\t{src_file}\tCould not create destination folder: {e}")
                        fail_count += 1
                        continue

                orig_name = os.path.basename(src_file)
                final_filename = new_name if new_name else orig_name
                target_path = os.path.join(dest_folder, final_filename)

                should_process = True

                if os.path.exists(target_path):
                    if overwrite_mode == 3:
                        self.log_message(f"[SKIPPED] Already exists: {target_path}")
                        report_rows.append(f"SKIPPED\t{src_file}\tTarget already exists (Skipped)")
                        should_process = False
                    elif overwrite_mode == 2:
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
                        if action == 2:
                            shutil.move(src_file, target_path)
                            self.undo_stack.append(("MOVE", src_file, target_path))
                            self.log_message(f"[MOVED] {src_file} -> {target_path}")
                            report_rows.append(f"MOVED\t{src_file}\t{target_path}")
                        else:
                            shutil.copy2(src_file, target_path)
                            self.undo_stack.append(("COPY", src_file, target_path))
                            self.log_message(f"[COPIED] {src_file} -> {target_path}")
                            report_rows.append(f"COPIED\t{src_file}\t{target_path}")
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[ERROR] Operation failed: {e}")
                        report_rows.append(f"ERROR\t{src_file}\tOperation failed: {e}")
                        fail_count += 1

        end_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_rows.append(f"Summary\tSuccessful: {success_count}\tFailed/Skipped: {fail_count}")
        report_rows.append(f"Session End\t{end_time_str}\t")

        self.log_message(f"\nOperation Complete! Successful: {success_count}, Failed/Skipped: {fail_count}")

        self.last_log_content = "\n".join(report_rows)
        self.btn_export_report.config(state=tk.NORMAL)
        if self.undo_stack:
            self.btn_undo.config(state=tk.NORMAL)

        try:
            auto_log_path = os.path.join(os.path.dirname(list_path), "AE_FileUtility_report.txt")
            with open(auto_log_path, "w", encoding="utf-8") as f:
                f.write(self.last_log_content)
        except Exception:
            pass

        messagebox.showinfo("Done", f"Operation finished!\nSuccessful: {success_count}\nFailed/Skipped: {fail_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileUtilityApp(root)
    root.mainloop()
