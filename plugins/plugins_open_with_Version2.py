plugin_info = {
    "name": "Open With...",
    "author": "MuZeRBLX Copilot",
    "version": "1.0.0",
    "trusted": True
}

def on_load(app, tools):
    tk = tools.modules["tkinter"]
    filedialog = tools.get_module("tkinter.filedialog")
    subprocess = tools.get_module("subprocess")
    os = tools.get_module("os")

    # Store recent apps by extension in memory (session only)
    recent_app_by_ext = {}

    def choose_app(ext):
        # Try to use a previously selected app for this extension
        initialdir = os.path.expanduser("~")
        app_path = None
        if ext in recent_app_by_ext:
            last_path = recent_app_by_ext[ext]
            if os.path.exists(last_path):
                app_path = last_path

        # Prompt: ask to pick an .exe or type command
        win = tk.Toplevel(app)
        win.title("Open With...")
        win.geometry("430x200")
        win.resizable(False, False)
        lbl = tk.Label(win, text="Select an application to open selected file(s):", font=("Segoe UI", 10))
        lbl.pack(pady=(10,2))

        app_path_var = tk.StringVar(value=app_path or "")

        def browse():
            file = filedialog.askopenfilename(
                title="Select Application",
                filetypes=[("Executable files", "*.exe;*.bat;*.cmd;*.app;*"), ("All files", "*.*")]
            )
            if file:
                app_path_var.set(file)

        entry = tk.Entry(win, textvariable=app_path_var, width=40, font=("Consolas", 10))
        entry.pack(pady=(5,2), padx=15)
        browse_btn = tk.Button(win, text="Browse...", command=browse)
        browse_btn.pack(pady=(2,2))

        lbl2 = tk.Label(win, text="Or enter a command (e.g. notepad.exe, code, etc):", font=("Segoe UI", 9))
        lbl2.pack(pady=(10,2))
        cmd_entry = tk.Entry(win, width=40, font=("Consolas", 10))
        cmd_entry.pack(pady=(2,10), padx=15)

        selected_command = {"value": None}

        def confirm():
            cmd = cmd_entry.get().strip()
            path = app_path_var.get().strip()
            if cmd:
                selected_command["value"] = cmd
                win.destroy()
            elif path:
                selected_command["value"] = path
                win.destroy()
            else:
                tools.run_error("Please select an application or enter a command.")

        ok_btn = tk.Button(win, text="Open", command=confirm)
        ok_btn.pack(side="left", padx=(80,10), pady=8)
        cancel_btn = tk.Button(win, text="Cancel", command=win.destroy)
        cancel_btn.pack(side="left", padx=10, pady=8)

        win.transient(app)
        win.grab_set()
        win.focus_force()
        entry.focus_set()
        win.wait_window()
        return selected_command["value"]

    def open_with(files):
        if not files:
            tools.run_error("No files selected.")
            return

        # Use the first selected file's extension for app memory
        ext = os.path.splitext(files[0])[1].lower()

        # Prompt for app/command if not already set
        if ext in recent_app_by_ext:
            use_last = tools.modules["tkinter"].messagebox.askyesno(
                "Open With...",
                f"Open with last used application for '{ext}'?\n({recent_app_by_ext[ext]})"
            )
            if use_last:
                chosen_app = recent_app_by_ext[ext]
            else:
                chosen_app = choose_app(ext)
        else:
            chosen_app = choose_app(ext)

        if not chosen_app:
            return  # User cancelled

        recent_app_by_ext[ext] = chosen_app

        current_dir = tools.GetCurrentPath()
        full_paths = [os.path.join(current_dir, f) for f in files]

        def run_open():
            try:
                # If it's a known executable or path, use it as app
                if os.path.isfile(chosen_app):
                    # Windows: always use list [app, file...]
                    for f in full_paths:
                        subprocess.Popen([chosen_app, f], shell=False)
                else:
                    # Assume command, e.g. 'notepad', 'code'
                    for f in full_paths:
                        subprocess.Popen(f"{chosen_app} \"{f}\"", shell=True)
                tools.show_noti(f"Opened {len(full_paths)} file(s) with: {os.path.basename(str(chosen_app))}")
                # Register a no-op undo for demo
                tools.add_undo({"action": "noop", "info": {}})
            except Exception as e:
                tools.run_error(f"Failed to open: {e}")

        tools.run_in_thread(run_open)

    def open_with_selected(event=None):
        files = tools.get_selected_filenames()
        open_with(files)

    # Register context menu command
    tools.AddContextMenuCommand("🗂️ Open With...", open_with_selected)

    # Optional: allow hotkey (Ctrl+Shift+O)
    tools.OnKeyPress("<Control-Shift-o>", lambda *_: open_with_selected())

    # Optional: event when pressing Enter on a file
    # tools.on_event("file_selected", lambda files: open_with(files) if len(files)==1 else None)