plugin_info = {
    "name": "Plugin Manager",
    "author": "MuZe",
    "version": "1.0.0",
    "description": "Manages Plugins",
    "trusted": True
}


def on_load(app, tools):
    
    print("🧩 Plugin Manager loaded")  # ← This should show up in logs
    ...
    tk = tools.modules["tkinter"]

    def show_plugin_manager():
        
        plugins = tools.context.get("plugins_loaded", [])
        if not plugins:
            tools.run_error("No plugins loaded.")
            return

        win = tk.Toplevel(app)
        win.title("🧩 Plugin Manager")
        win.geometry("400x300")
        win.configure(bg="#1e1e1e")

        header = tk.Label(win, text="Installed Plugins", bg="#1e1e1e", fg="#80cbc4", font=("Segoe UI", 14, "bold"))
        header.pack(pady=(10, 4))

        frame = tk.Frame(win, bg="#1e1e1e")
        frame.pack(fill="both", expand=True)

        for plugin in plugins:
            info = getattr(plugin, "_info", {})
            name = info.get("name", plugin.__name__)
            author = info.get("author", "Unknown")
            version = info.get("version", "0.0")
            trusted = info.get("trusted", False)

            label = tk.Label(
                frame,
                text=f"{name} v{version} by {author}" + (" ✅" if trusted else " ⚠️"),
                anchor="w",
                bg="#2a2a2a",
                fg="#ccc",
                font=("Segoe UI", 10),
                padx=10,
                pady=5
            )
            label.pack(fill="x", padx=10, pady=2)

        win.transient(app)
        win.grab_set()
        win.focus_force()

    # Bind to F10 or your choice
    def debug_key(key):
        print(f"[PLUGIN DEBUG] received key: {key}")

    tools.on_event("key_pressed", debug_key)
    tools.OnKeyPress("<Control-p>", lambda: print("[DEBUG] Ctrl+P bound"))
    tools.OnKeyPress("<Control-p>", show_plugin_manager)