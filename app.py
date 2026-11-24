import os
import json
import shutil
import sys
import time
import threading
import urllib.request
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime, timedelta

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    HAS_DND = False
    TkinterDnD = None
    DND_FILES = None

CONFIG_FILE = "AE_FileUtility_config.json"
UNDO_STATE_FILE = "AE_FileUtility_last_undo.json"
CURRENT_VERSION = "1.3.3"
GITHUB_REPO = "ahmedbahgatz2data-collab/AE_FileUtility"


class FileUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"AE_FileUtility - Ultimate File Manager (v{CURRENT_VERSION})")
        self.root.geometry("830x790")
        self.root.minsize(730, 690)

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
        style.map(
            "Primary.TButton",
            background=[("active", self.primary_hover), ("pressed", "#1e40af")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
        )

        self.list_path_var = tk.StringVar()
        self.filter_ext_var = tk.StringVar(value="")
        self.filter_days_var = tk.StringVar(value="")
        self.filter_time_mode_var = tk.StringVar(value="within")
        self.filter_name_var = tk.StringVar(value="")
        self.filter_max_mb_var = tk.StringVar(value="")

        self.action_choice = tk.IntVar(value=1)
        self.overwrite_choice = tk.IntVar(value=1)
        self.last_log_content = ""
        self.undo_stack = []
        self.is_busy = False
        self.update_ready = False

        self.load_settings()
        self.load_persisted_undo()
        self.create_widgets()
        self.bind_drag_and_drop()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        threading.Thread(target=self.check_updates_worker, args=(False,), daemon=True).start()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=14)
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.LabelFrame(main_frame, text=" 📥 Quick Start & Updates ", padding=8)
        top_bar.pack(fill=tk.X, pady=(0, 8))

        dnd_status = "Drag & Drop Active" if HAS_DND else "Browse / Path Input"
        lbl_tip = ttk.Label(top_bar, text=f"Tab-delimited TXT template ({dnd_status}).")
        lbl_tip.pack(side=tk.LEFT, padx=5)

        self.btn_check_update = ttk.Button(top_bar, text="🔄 Check for Updates", command=self.manual_check_updates)
        self.btn_check_update.pack(side=tk.RIGHT, padx=(4, 0))

        btn_download_template = ttk.Button(top_bar, text="Download Template", command=self.download_template)
        btn_download_template.pack(side=tk.RIGHT, padx=4)

        file_frame = ttk.LabelFrame(main_frame, text=" 📂 1. TXT List & Smart Filters ", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 8))

        f_top = ttk.Frame(file_frame)
        f_top.pack(fill=tk.X, pady=2)
        self.entry_path = ttk.Entry(f_top, textvariable=self.list_path_var, font=("Segoe UI", 10))
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse = ttk.Button(f_top, text="Browse...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        f_row1 = ttk.Frame(file_frame)
        f_row1.pack(fill=tk.X, pady=(8, 2))

        ttk.Label(f_row1, text="Ext:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_filter_ext = ttk.Entry(f_row1, textvariable=self.filter_ext_var, width=8)
        self.entry_filter_ext.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(f_row1, text="Days:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_filter_days = ttk.Entry(f_row1, textvariable=self.filter_days_var, width=6)
        self.entry_filter_days.pack(side=tk.LEFT, padx=(0, 6))

        self.cb_time_mode = ttk.Combobox(
            f_row1,
            textvariable=self.filter_time_mode_var,
            values=["within", "older"],
            width=8,
            state="readonly",
        )
        self.cb_time_mode.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(f_row1, text="Name contains:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_filter_name = ttk.Entry(f_row1, textvariable=self.filter_name_var, width=14)
        self.entry_filter_name.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(f_row1, text="Max MB:").pack(side=tk.LEFT, padx=(0, 4))
        self.entry_filter_mb = ttk.Entry(f_row1, textvariable=self.filter_max_mb_var, width=7)
        self.entry_filter_mb.pack(side=tk.LEFT)

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

        action_btns = ttk.Frame(main_frame)
        action_btns.pack(fill=tk.X, pady=(0, 5))

        self.btn_preview = ttk.Button(action_btns, text="🔍 Preview (Dry-Run)", command=self.start_preview_thread)
        self.btn_preview.pack(side=tk.LEFT, padx=(0, 8), ipadx=6)

        self.btn_run = ttk.Button(action_btns, text="🚀 Start Operation", command=self.start_run_thread, style="Primary.TButton")
        self.btn_run.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 8))

        log_frame = ttk.LabelFrame(main_frame, text=" 💻 Live Output & Logs ", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, bg="#1e1e1e", fg="#4ec9b0", font=("Consolas", 9), bd=0, highlightthickness=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        bottom_bar = ttk.Frame(main_frame)
        bottom_bar.pack(fill=tk.X)

        undo_state = tk.NORMAL if self.undo_stack else tk.DISABLED
        self.btn_undo = ttk.Button(bottom_bar, text="↩️ Undo Last Operation", command=self.undo_operation, state=undo_state)
        self.btn_undo.pack(side=tk.LEFT)

        self.btn_export_report = ttk.Button(bottom_bar, text="📊 Download Tab-Delimited Report", command=self.export_report, state=tk.DISABLED)
        self.btn_export_report.pack(side=tk.RIGHT)

        self.toggle_overwrite_state()

    def bind_drag_and_drop(self):
        if not HAS_DND or DND_FILES is None:
            return
        for widget in (self.root, self.entry_path):
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self.on_drop_items)
            except Exception:
                pass

    def _parse_dropped_paths(self, data_str):
        paths = []
        current = []
        in_braces = False
        for ch in data_str:
            if ch == "{":
                in_braces = True
                current = []
            elif ch == "}":
                in_braces = False
                val = "".join(current).strip()
                if val:
                    paths.append(val)
                current = []
            elif ch == " " and not in_braces:
                val = "".join(current).strip()
                if val:
                    paths.append(val)
                current = []
            else:
                current.append(ch)
        tail = "".join(current).strip()
        if tail:
            paths.append(tail)
        return paths

    def on_drop_items(self, event):
        paths = self._parse_dropped_paths(event.data or "")
        if not paths:
            return

        if len(paths) == 1 and paths[0].lower().endswith(".txt") and os.path.isfile(paths[0]):
            self.list_path_var.set(paths[0])
            self.log_message(f"[DND] Loaded TXT list: {paths[0]}")
            return

        collected_files = []
        for p in paths:
            if os.path.isfile(p):
                collected_files.append(p)
            elif os.path.isdir(p):
                for root_dir, _, files in os.walk(p):
                    for fn in files:
                        collected_files.append(os.path.join(root_dir, fn))

        if not collected_files:
            self.log_message("[DND] No files found in dropped items.")
            return

        temp_dir = os.environ.get("TEMP", os.getcwd())
        generated_list = os.path.join(temp_dir, "AE_FileUtility_dnd_list.txt")
        try:
            with open(generated_list, "w", encoding="utf-8") as f:
                f.write("# Auto-generated from Drag & Drop\n")
                for fp in collected_files:
                    f.write(f"{fp}\t\t\n")
            self.list_path_var.set(generated_list)
            self.log_message(f"[DND] Generated list with {len(collected_files)} files -> {generated_list}")
        except Exception as e:
            self.log_message(f"[DND ERROR] Could not create list: {e}")

    def manual_check_updates(self):
        self.btn_check_update.config(state=tk.DISABLED)
        self.log_message("[UPDATE] Checking GitHub releases...")
        threading.Thread(target=self.check_updates_worker, args=(True,), daemon=True).start()

    def _fetch_url_with_retry(self, url, timeout=15, retries=3, bypass_proxy=False):
        last_err = None
        openers = []
        if bypass_proxy:
            openers.append(urllib.request.build_opener(urllib.request.ProxyHandler({})))
        openers.append(urllib.request.build_opener())

        for opener in openers:
            for attempt in range(1, retries + 1):
                try:
                    req = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "AE_FileUtility-Updater",
                            "Accept": "application/vnd.github+json",
                            "Connection": "close",
                        },
                    )
                    with opener.open(req, timeout=timeout) as resp:
                        return resp.read()
                except Exception as e:
                    last_err = e
                    if attempt < retries:
                        time.sleep(1.5 * attempt)
        raise last_err if last_err else RuntimeError("Network request failed")

    def _download_file_with_retry(self, url, dest_path, timeout=45, retries=3):
        last_err = None
        for opener in (urllib.request.build_opener(), urllib.request.build_opener(urllib.request.ProxyHandler({}))):
            for attempt in range(1, retries + 1):
                try:
                    req = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "AE_FileUtility-Updater",
                            "Connection": "close",
                        },
                    )
                    with opener.open(req, timeout=timeout) as dl_resp, open(dest_path, "wb") as out_f:
                        shutil.copyfileobj(dl_resp, out_f)
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                        return
                except Exception as e:
                    last_err = e
                    try:
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                    except Exception:
                        pass
                    if attempt < retries:
                        time.sleep(2 * attempt)
        raise last_err if last_err else RuntimeError("Download failed")

    def check_updates_worker(self, verbose=False):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            try:
                raw_bytes = self._fetch_url_with_retry(api_url, timeout=15, retries=3, bypass_proxy=False)
            except Exception:
                raw_bytes = self._fetch_url_with_retry(api_url, timeout=15, retries=2, bypass_proxy=True)

            data = json.loads(raw_bytes.decode("utf-8"))
            latest_tag = str(data.get("tag_name", "")).strip()
            latest_version = latest_tag.lstrip("vV")

            if not latest_version or latest_version == CURRENT_VERSION.lstrip("vV"):
                if verbose:
                    self.root.after(0, lambda: self.log_message(f"[UPDATE] Already on latest version (v{CURRENT_VERSION})."))
                    self.root.after(0, lambda: messagebox.showinfo("Updates", f"You are already using the latest version (v{CURRENT_VERSION})."))
                return

            if not getattr(sys, "frozen", False):
                if verbose:
                    self.root.after(0, lambda v=latest_tag: self.log_message(f"[UPDATE] Newer release available: {v} (running from source)."))
                return

            asset_found = False
            for asset in data.get("assets", []):
                if asset.get("name") == "AE_FileUtility.exe":
                    asset_found = True
                    download_url = asset.get("browser_download_url")
                    if not download_url:
                        break

                    temp_dir = os.environ.get("TEMP", os.getcwd())
                    temp_exe = os.path.join(temp_dir, "AE_FileUtility_update_new.exe")
                    batch_path = os.path.join(temp_dir, "AE_FileUtility_apply_update.bat")
                    current_exe = sys.executable
                    current_pid = os.getpid()

                    self._download_file_with_retry(download_url, temp_exe, timeout=45, retries=3)

                    bat_script = (
                        "@echo off\n"
                        "setlocal\n"
                        f"set \"PID={current_pid}\"\n"
                        f"set \"NEW_EXE={temp_exe}\"\n"
                        f"set \"TARGET_EXE={current_exe}\"\n"
                        ":wait_loop\n"
                        "tasklist /FI \"PID eq %PID%\" 2>nul | find \"%PID%\" >nul\n"
                        "if not errorlevel 1 (\n"
                        "    timeout /t 1 /nobreak >nul\n"
                        "    goto wait_loop\n"
                        ")\n"
                        "timeout /t 1 /nobreak >nul\n"
                        "move /y \"%NEW_EXE%\" \"%TARGET_EXE%\" >nul 2>&1\n"
                        "if errorlevel 1 (\n"
                        "    copy /y \"%NEW_EXE%\" \"%TARGET_EXE%\" >nul 2>&1\n"
                        "    del /f /q \"%NEW_EXE%\" >nul 2>&1\n"
                        ")\n"
                        "start \"\" \"%TARGET_EXE%\"\n"
                        "del /f /q \"%~f0\" >nul 2>&1\n"
                    )
                    with open(batch_path, "w", encoding="utf-8") as b_file:
                        b_file.write(bat_script)

                    self.update_ready = True
                    self.root.after(0, lambda v=latest_tag: self.log_message(f"[UPDATE] {v} downloaded silently; will apply on exit."))
                    if verbose:
                        self.root.after(
                            0,
                            lambda v=latest_tag: messagebox.showinfo(
                                "Update Ready", f"Version {v} has been downloaded and will apply automatically when you close the app."
                            ),
                        )
                    break

            if not asset_found and verbose:
                self.root.after(0, lambda v=latest_tag: self.log_message(f"[UPDATE] Release {v} found, but AE_FileUtility.exe asset was not attached."))
        except Exception as e:
            if verbose:
                self.root.after(0, lambda err=e: self.log_message(f"[UPDATE] Check failed: {err}"))
        finally:
            if verbose:
                self.root.after(0, lambda: self.btn_check_update.config(state=tk.NORMAL))

    def toggle_overwrite_state(self):
        state = tk.DISABLED if self.action_choice.get() == 3 else tk.NORMAL
        self.rb_ow_1.config(state=state)
        self.rb_ow_2.config(state=state)
        self.rb_ow_3.config(state=state)

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.action_choice.set(data.get("action", 1))
                    self.overwrite_choice.set(data.get("overwrite", 1))
                    self.filter_ext_var.set(data.get("filter_ext", ""))
                    self.filter_days_var.set(data.get("filter_days", ""))
                    self.filter_time_mode_var.set(data.get("filter_time_mode", "within"))
                    self.filter_name_var.set(data.get("filter_name", ""))
                    self.filter_max_mb_var.set(data.get("filter_max_mb", ""))
            except Exception:
                pass

    def save_settings(self):
        data = {
            "action": self.action_choice.get(),
            "overwrite": self.overwrite_choice.get(),
            "filter_ext": self.filter_ext_var.get(),
            "filter_days": self.filter_days_var.get(),
            "filter_time_mode": self.filter_time_mode_var.get(),
            "filter_name": self.filter_name_var.get(),
            "filter_max_mb": self.filter_max_mb_var.get(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def load_persisted_undo(self):
        if os.path.exists(UNDO_STATE_FILE):
            try:
                with open(UNDO_STATE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        self.undo_stack = loaded
            except Exception:
                pass

    def save_persisted_undo(self):
        try:
            with open(UNDO_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.undo_stack, f)
        except Exception:
            pass

    def on_close(self):
        self.save_settings()
        self.save_persisted_undo()
        batch_path = os.path.join(os.environ.get("TEMP", os.getcwd()), "AE_FileUtility_apply_update.bat")
        try:
            self.root.destroy()
        finally:
            if os.path.exists(batch_path):
                try:
                    os.startfile(batch_path)
                except Exception:
                    pass

    def download_template(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="AE_FileUtility_template.txt",
            title="Save Template File",
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

    def set_busy_state(self, busy):
        self.is_busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_run.config(state=state)
        self.btn_preview.config(state=state)
        self.btn_check_update.config(state=state)
        if not busy:
            self.btn_undo.config(state=tk.NORMAL if self.undo_stack else tk.DISABLED)
            self.btn_export_report.config(state=tk.NORMAL if self.last_log_content else tk.DISABLED)

    def get_file_metadata(self, path):
        try:
            st = os.stat(path)
            size_kb = f"{st.st_size / 1024:.1f}"
            mtime_str = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            return size_kb, mtime_str, st.st_size, datetime.fromtimestamp(st.st_mtime)
        except Exception:
            return "0.0", "", 0, None

    def matches_filters(self, src_file, file_size_bytes, file_mtime, filter_ext, max_days, time_mode, name_substr, max_bytes):
        if filter_ext:
            _, ext = os.path.splitext(src_file)
            if ext.lower() != filter_ext:
                return False, f"Extension mismatch ({ext or 'none'})"

        if name_substr:
            base = os.path.basename(src_file).lower()
            if name_substr not in base:
                return False, f"Name does not contain '{name_substr}'"

        if max_bytes is not None and file_size_bytes > max_bytes:
            actual_mb = file_size_bytes / (1024 * 1024)
            return False, f"Size {actual_mb:.2f} MB exceeds max {max_bytes / (1024 * 1024):.2f} MB"

        if max_days is not None and file_mtime is not None:
            threshold = datetime.now() - timedelta(days=max_days)
            if time_mode == "within" and file_mtime < threshold:
                return False, f"Older than {max_days} days"
            if time_mode == "older" and file_mtime >= threshold:
                return False, f"Modified within last {max_days} days"

        return True, ""

    def resolve_target(self, src_file, dest_folder, new_name, action, overwrite_mode):
        if action == 3:
            if not new_name:
                return None, "SKIPPED", "No new name provided"
            src_folder, old_name = os.path.split(src_file)
            _, old_ext = os.path.splitext(old_name)
            target_name = new_name if os.path.splitext(new_name)[1] else new_name + old_ext
            target_path = os.path.join(src_folder, target_name)
            if os.path.abspath(src_file).lower() == os.path.abspath(target_path).lower():
                return None, "SKIPPED", "Name is identical"
            if os.path.exists(target_path):
                return None, "ERROR", f"Target already exists: {target_path}"
            return target_path, "OK", target_path

        if not dest_folder:
            return None, "ERROR", "No destination specified"

        orig_name = os.path.basename(src_file)
        final_filename = new_name if new_name else orig_name
        target_path = os.path.join(dest_folder, final_filename)

        if os.path.exists(target_path):
            if overwrite_mode == 3:
                return None, "SKIPPED", "Target already exists (Skipped)"
            if overwrite_mode == 2:
                base_n, ext_n = os.path.splitext(final_filename)
                count = 1
                while True:
                    test_name = f"{base_n}_{count}{ext_n}"
                    test_path = os.path.join(dest_folder, test_name)
                    if not os.path.exists(test_path):
                        target_path = test_path
                        break
                    count += 1

        return target_path, "OK", target_path

    def export_report(self):
        if not self.last_log_content:
            messagebox.showwarning("Warning", "No logs to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="AE_FileUtility_report.txt",
            title="Save Tab-Delimited Report",
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

        self.save_persisted_undo()
        self.log_message(f"Undo Complete! Successfully reverted {success_undo} items.")
        messagebox.showinfo("Undo Finished", f"Successfully reverted {success_undo} actions.")
        self.btn_undo.config(state=tk.DISABLED)

    def start_preview_thread(self):
        if not self.is_busy:
            threading.Thread(target=self._execute_job, args=(True,), daemon=True).start()

    def start_run_thread(self):
        if not self.is_busy:
            threading.Thread(target=self._execute_job, args=(False,), daemon=True).start()

    def _execute_job(self, dry_run):
        list_path = self.list_path_var.get().strip()
        if not list_path or not os.path.exists(list_path):
            self.root.after(0, lambda: messagebox.showerror("Error", "Please select a valid TXT configuration file first!"))
            return

        self.save_settings()
        self.root.after(0, lambda: self.set_busy_state(True))
        self.root.after(0, lambda: self.log_text.delete("1.0", tk.END))

        action = self.action_choice.get()
        overwrite_mode = self.overwrite_choice.get()

        filter_ext = self.filter_ext_var.get().strip().lower()
        if filter_ext and not filter_ext.startswith("."):
            filter_ext = "." + filter_ext

        filter_days_str = self.filter_days_var.get().strip()
        max_days = int(filter_days_str) if filter_days_str.isdigit() else None
        time_mode = self.filter_time_mode_var.get()

        name_substr = self.filter_name_var.get().strip().lower()

        max_mb_str = self.filter_max_mb_var.get().strip()
        max_bytes = None
        if max_mb_str:
            try:
                max_bytes = float(max_mb_str) * 1024 * 1024
            except ValueError:
                max_bytes = None

        try:
            with open(list_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", f"Could not read file: {err}"))
            self.root.after(0, lambda: self.set_busy_state(False))
            return

        total_lines = len(lines)
        if total_lines == 0:
            self.root.after(0, lambda: messagebox.showwarning("Warning", "The configuration file is empty!"))
            self.root.after(0, lambda: self.set_busy_state(False))
            return

        self.root.after(0, lambda: self.progress.configure(maximum=total_lines, value=0))

        mode_label = "DRY-RUN PREVIEW" if dry_run else "LIVE OPERATION"
        start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.root.after(0, lambda m=mode_label, t=start_time_str: self.log_message(f"AE_FileUtility [{m}] Started: {t}"))

        report_rows = [
            f"Mode\t{mode_label}\t{start_time_str}\t\t\t",
            "Status\tSource File\tDestination / Result\tSize (KB)\tModified Date\tDetails",
        ]

        if not dry_run:
            self.undo_stack = []

        success_count = 0
        fail_count = 0
        filtered_count = 0

        for idx, line in enumerate(lines, start=1):
            self.root.after(0, lambda v=idx: self.progress.configure(value=v))

            parts = line.split("\t")
            src_file = parts[0].strip() if len(parts) > 0 else ""
            dest_folder = parts[1].strip() if len(parts) > 1 else ""
            new_name = parts[2].strip() if len(parts) > 2 else ""

            if not src_file:
                continue

            if not os.path.exists(src_file):
                self.root.after(0, lambda s=src_file: self.log_message(f"[NOT FOUND] {s}"))
                report_rows.append(f"NOT FOUND\t{src_file}\t\t0.0\t\tFile does not exist")
                fail_count += 1
                continue

            size_kb, mtime_str, f_bytes, f_mtime = self.get_file_metadata(src_file)

            passed, reason = self.matches_filters(
                src_file, f_bytes, f_mtime, filter_ext, max_days, time_mode, name_substr, max_bytes
            )
            if not passed:
                filtered_count += 1
                report_rows.append(f"FILTERED\t{src_file}\t\t{size_kb}\t{mtime_str}\t{reason}")
                continue

            target_path, status_code, detail_or_path = self.resolve_target(
                src_file, dest_folder, new_name, action, overwrite_mode
            )

            if status_code != "OK":
                self.root.after(0, lambda st=status_code, s=src_file, d=detail_or_path: self.log_message(f"[{st}] {s} -> {d}"))
                report_rows.append(f"{status_code}\t{src_file}\t\t{size_kb}\t{mtime_str}\t{detail_or_path}")
                if status_code == "ERROR":
                    fail_count += 1
                continue

            planned_verb = "RENAME" if action == 3 else ("MOVE" if action == 2 else "COPY")

            if dry_run:
                self.root.after(
                    0,
                    lambda pv=planned_verb, s=src_file, t=target_path: self.log_message(f"[PREVIEW {pv}] {s} -> {t}"),
                )
                report_rows.append(f"PREVIEW_{planned_verb}\t{src_file}\t{target_path}\t{size_kb}\t{mtime_str}\tDry-run only")
                success_count += 1
                continue

            try:
                if action == 3:
                    os.rename(src_file, target_path)
                    self.undo_stack.append(("RENAME", src_file, target_path))
                    self.root.after(0, lambda s=src_file, t=target_path: self.log_message(f"[RENAMED] {s} -> {t}"))
                    report_rows.append(f"RENAMED\t{src_file}\t{target_path}\t{size_kb}\t{mtime_str}\tRenamed in-place")
                elif action == 2:
                    if dest_folder and not os.path.exists(dest_folder):
                        os.makedirs(dest_folder)
                    shutil.move(src_file, target_path)
                    self.undo_stack.append(("MOVE", src_file, target_path))
                    self.root.after(0, lambda s=src_file, t=target_path: self.log_message(f"[MOVED] {s} -> {t}"))
                    report_rows.append(f"MOVED\t{src_file}\t{target_path}\t{size_kb}\t{mtime_str}\tMoved")
                else:
                    if dest_folder and not os.path.exists(dest_folder):
                        os.makedirs(dest_folder)
                    shutil.copy2(src_file, target_path)
                    self.undo_stack.append(("COPY", src_file, target_path))
                    self.root.after(0, lambda s=src_file, t=target_path: self.log_message(f"[COPIED] {s} -> {t}"))
                    report_rows.append(f"COPIED\t{src_file}\t{target_path}\t{size_kb}\t{mtime_str}\tCopied")
                success_count += 1
            except Exception as e:
                self.root.after(0, lambda s=src_file, err=e: self.log_message(f"[ERROR] {s}: {err}"))
                report_rows.append(f"ERROR\t{src_file}\t{target_path}\t{size_kb}\t{mtime_str}\t{e}")
                fail_count += 1

        if not dry_run:
            self.save_persisted_undo()

        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_rows.append(f"Summary\tMatched/Done: {success_count}\tFailed: {fail_count}\tFiltered: {filtered_count}\t{end_time_str}\t")

        summary_msg = f"\n{mode_label} Complete! Matched/Done: {success_count}, Failed: {fail_count}, Filtered: {filtered_count}"
        self.root.after(0, lambda msg=summary_msg: self.log_message(msg))

        self.last_log_content = "\n".join(report_rows)

        if not dry_run:
            try:
                auto_log_path = os.path.join(os.path.dirname(list_path), "AE_FileUtility_report.txt")
                with open(auto_log_path, "w", encoding="utf-8") as f:
                    f.write(self.last_log_content)
            except Exception:
                pass

        self.root.after(0, lambda: self.set_busy_state(False))
        self.root.after(
            0,
            lambda m=mode_label, ok=success_count, fl=fail_count, ft=filtered_count: messagebox.showinfo(
                "Done", f"{m} finished!\nMatched/Done: {ok}\nFailed: {fl}\nFiltered: {ft}"
            ),
        )


if __name__ == "__main__":
    if HAS_DND and TkinterDnD is not None:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = FileUtilityApp(root)
    root.mainloop()
