import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

class FileUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AE_FileUtility - Pro File Manager")
        self.root.geometry("720x640")
        self.root.minsize(650, 580)

        # Configure Modern Styles & Palette
        style = ttk.Style()
        style.theme_use("clam")

        # Color Palette Definition
        self.bg_color = "#f4f6f9"
        self.primary_color = "#2563eb"  # Modern Royal Blue
        self.primary_hover = "#1d4ed8"
        self.text_color = "#1f2937"
        self.border_color = "#d1d5db"

        self.root.configure(bg=self.bg_color)

        # Configure TTK Styles
        style.configure(".", font=("Segoe UI", 10), background=self.bg_color, foreground=self.text_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
        style.configure("TLabelframe", background=self.bg_color, bordercolor=self.border_color, borderwidth=1)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), background=self.bg_color, foreground=self.primary_color)
        
        # Standard Button Style
        style.configure("TButton", font=("Segoe UI", 10), padding=6, relief="flat", background="#e5e7eb")
        style.map("TButton", background=[("active", "#d1d5db"), ("pressed", "#9ca3af")])

        # Primary Action Button Style
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="#ffffff", padding=8)
        style.map("Primary.TButton", 
                  background=[("active", self.primary_hover), ("pressed", "#1e40af")],
                  foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])

        # Variables
        self.list_path_var = tk.StringVar()
        self.action_choice = tk.IntVar(value=1)
        self.overwrite_choice = tk.IntVar(value=1)
        self.last_log_content = ""

        self.create_widgets()

    def create_widgets(self):
        # Main Container with Padding
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 0. Template Download Section (Styled Banner)
        template_frame = ttk.LabelFrame(main_frame, text=" 📥 Quick Start Template ", padding=10)
        template_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_tip = ttk.Label(template_frame, text="Download the TXT template. It includes clear instructions & examples for all 3 operations.")
        lbl_tip.pack(side=tk.LEFT, padx=5)

        btn_download_template = ttk.Button(template_frame, text="Download Template", command=self.download_template)
        btn_download_template.pack(side=tk.RIGHT, padx=5)

        # 1. File Selection Section
        file_frame = ttk.LabelFrame(main_frame, text=" 📂 1. Select TXT Configuration File ", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.entry_path = ttk.Entry(file_frame, textvariable=self.list_path_var, font=("Segoe UI", 10))
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Options Container (Side by Side Frames)
        options_container = ttk.Frame(main_frame)
        options_container.pack(fill=tk.X, pady=(0, 10))

        # 2. Action Choice
        action_frame = ttk.LabelFrame(options_container, text=" ⚙️ 2. Choose Action ", padding=10)
        action_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Radiobutton(action_frame, text="Copy files", variable=self.action_choice, value=1, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=3)
        ttk.Radiobutton(action_frame, text="Move files", variable=self.action_choice, value=2, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=3)
        ttk.Radiobutton(action_frame, text="Rename in-place only", variable=self.action_choice, value=3, command=self.toggle_overwrite_state).pack(anchor=tk.W, pady=3)

        # 3. Overwrite Mode
        self.overwrite_frame = ttk.LabelFrame(options_container, text=" 🔄 3. Overwrite Mode ", padding=10)
        self.overwrite_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.rb_ow_1 = ttk.Radiobutton(self.overwrite_frame, text="Overwrite existing", variable=self.overwrite_choice, value=1)
        self.rb_ow_1.pack(anchor=tk.W, pady=3)
        self.rb_ow_2 = ttk.Radiobutton(self.overwrite_frame, text="Auto-number duplicates", variable=self.overwrite_choice, value=2)
        self.rb_ow_2.pack(anchor=tk.W, pady=3)
        self.rb_ow_3 = ttk.Radiobutton(self.overwrite_frame, text="Skip existing", variable=self.overwrite_choice, value=3)
        self.rb_ow_3.pack(anchor=tk.W, pady=3)

        # Run Button
        self.btn_run = ttk.Button(main_frame, text="🚀 Start Operation", command=self.run_operation, style="Primary.TButton")
        self.btn_run.pack(fill=tk.X, pady=(0, 10))

        # Log Console Area
        log_frame = ttk.LabelFrame(main_frame, text=" 💻 Live Output & Logs ", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=11, bg="#1e1e1e", fg="#4ec9b0", font=("Consolas", 9), bd=0, highlightthickness=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Bottom Bar for Report Export
        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X)

        self.btn_export_report = ttk.Button(bottom_bar, text="📊 Download Tab-Delimited Report", command=self.export_report, state=tk.DISABLED)
        self.btn_export_report.pack(side=tk.RIGHT)

    def toggle_overwrite_state(self):
        if self.action_choice.get() == 3:
            self.rb_ow_1.config(state=tk.DISABLED)
            self.rb_ow_2.config(state=tk.DISABLED)
            self.rb_ow_3.config(state=tk.DISABLED)
        else:
            self.rb_ow_1.config(state=tk.NORMAL)
            self.rb_ow_2.config(state=tk.NORMAL)
            self.rb_ow_3.config(state=tk.NORMAL)

    def download_template(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="AE_FileUtility_template.txt",
            title="Save Template File"
        )
        if file_path:
            # Template containing explicit instructions and examples separated by TAB
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
                messagebox.showinfo("Success", f"Template file with instructions successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save template file: {e}")

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
            messagebox.showwarning("Warning", "No operation logs available to export yet.")
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
                messagebox.showinfo("Success", f"Tab-delimited report successfully saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save report: {e}")

    def run_operation(self):
        list_path = self.list_path_var.get().strip()
        if not list_path or not os.path.exists(list_path):
            messagebox.showerror("Error", "Please select a valid TXT configuration file first!")
            return

        self.log_text.delete("1.0", tk.END)
        
        report_rows = []
        action = self.action_choice.get()
        overwrite_mode = self.overwrite_choice.get()

        start_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.log_message("===================================================")
        self.log_message(f"AE_FileUtility Session Started: {start_time_str}")
        self.log_message("===================================================")
        
        report_rows.append(f"Session Start\t{start_time_str}\t")
        report_rows.append("Status\tSource File\tDestination / Result")

        success_count = 0
        fail_count = 0

        try:
            with open(list_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")
            return

        for line in lines:
            line_str = line.strip()
            # Skip comment lines starting with '#' or empty lines
            if not line_str or line_str.startswith("#"):
                continue

            parts = line_str.split("\t")
            src_file = parts[0].strip() if len(parts) > 0 else ""
            dest_folder = parts[1].strip() if len(parts) > 1 else ""
            new_name = parts[2].strip() if len(parts) > 2 else ""

            if not src_file:
                continue

            if not os.path.exists(src_file):
                self.log_message(f"[NOT FOUND] {src_file}")
                report_rows.append(f"NOT FOUND\t{src_file}\tFile does not exist on disk")
                fail_count += 1
                continue

            # ACTION 3: RENAME IN-PLACE
            if action == 3:
                if not new_name:
                    self.log_message(f"[SKIPPED] No new name provided: {src_file}")
                    report_rows.append(f"SKIPPED\t{src_file}\tNo new name provided for in-place rename")
                    continue
                
                src_folder, old_name = os.path.split(src_file)
                base_name, old_ext = os.path.splitext(old_name)
                
                if not os.path.splitext(new_name)[1]:
                    target_name = new_name + old_ext
                else:
                    target_name = new_name

                target_path = os.path.join(src_folder, target_name)

                if os.path.abspath(src_file).lower() == os.path.abspath(target_path).lower():
                    self.log_message(f"[SKIPPED] Name is identical: {src_file}")
                    report_rows.append(f"SKIPPED\t{src_file}\tNew name is identical to current name")
                elif os.path.exists(target_path):
                    self.log_message(f"[ERROR] Target already exists: {target_path}")
                    report_rows.append(f"ERROR\t{src_file}\tTarget already exists: {target_path}")
                    fail_count += 1
                else:
                    try:
                        os.rename(src_file, target_path)
                        self.log_message(f"[RENAMED] {src_file} -> {target_name}")
                        report_rows.append(f"RENAMED\t{src_file}\t{target_path}")
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[ERROR] Failed to rename: {e}")
                        report_rows.append(f"ERROR\t{src_file}\tFailed to rename: {e}")
                        fail_count += 1

            # ACTIONS 1 & 2: COPY OR MOVE
            else:
                if not dest_folder:
                    self.log_message(f"[ERROR] No destination specified for: {src_file}")
                    report_rows.append(f"ERROR\t{src_file}\tNo destination folder specified")
                    fail_count += 1
                    continue

                if not os.path.exists(dest_folder):
                    try:
                        os.makedirs(dest_folder)
                    except Exception as e:
                        self.log_message(f"[ERROR] Could not create folder {dest_folder}: {e}")
                        report_rows.append(f"ERROR\t{src_file}\tCould not create destination folder: {e}")
                        fail_count += 1
                        continue

                orig_name = os.path.basename(src_file)
                final_filename = new_name if new_name else orig_name
                target_path = os.path.join(dest_folder, final_filename)

                should_process = True

                if os.path.exists(target_path):
                    if overwrite_mode == 3: # Skip
                        self.log_message(f"[SKIPPED] Already exists: {target_path}")
                        report_rows.append(f"SKIPPED\t{src_file}\tTarget already exists (Skipped): {target_path}")
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
                            report_rows.append(f"MOVED\t{src_file}\t{target_path}")
                        else: # Copy
                            shutil.copy2(src_file, target_path)
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

        self.log_message("===================================================")
        self.log_message(f"   Operation Complete!")
        self.log_message(f"   Successful: {success_count}")
        self.log_message(f"   Failed / Skipped: {fail_count}")
        self.log_message("===================================================")
        self.log_message(f"Session Ended: {end_time_str}")

        self.last_log_content = "\n".join(report_rows)
        self.btn_export_report.config(state=tk.NORMAL)

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
