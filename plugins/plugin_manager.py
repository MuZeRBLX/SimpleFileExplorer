plugin_info = {
    "name": "Plugin Manager",
    "author": "MuZe",
    "version": "1.0.0",
    "description": "Manages Plugins",
    "trusted": True
}


def on_load(app, tools):
    
    print("🧩 Plugin Manager loaded")
    tk = tools.modules["tkinter"]

    def show_plugin_manager():
        plugins = tools.context.get("plugins_loaded", [])
        if not plugins:
            tools.run_error("No plugins loaded.")
            return

        win = tk.Toplevel(app)
        win.title("🧩 Plugin Manager")
        win.geometry("400x400")
        win.configure(bg="#1e1e1e")

        header = tk.Label(win, text="🧩 Installed Plugins 🧩", bg="#1e1e1e", fg="#80cbc4", font=("Segoe UI", 14, "bold"))
        header.pack(pady=(10, 4))

        # 🖼️ Canvas + Scrollbar setup
        container = tk.Frame(win, bg="#1e1e1e")
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 🧩 Add plugins inside the scrollable frame
        for plugin in plugins:
            info = getattr(plugin, "_info", {})
            name = info.get("name", plugin.__name__)
            author = info.get("author", "Unknown")
            desc = info.get("description", "Unknown Description")
            version = info.get("version", "0.0")
            trusted = info.get("trusted", False)

            frame2 = tk.Frame(scrollable_frame, bg="#2a2a2a")
            frame2.pack(fill="both", pady=5, padx=5)

            label = tk.Label(
                frame2,
                text=f"{name} v{version} by {author}" + (" ✅" if trusted else " ⚠️"),
                anchor="w",
                bg="#2a2a2a",
                fg="#ccc",
                font=("Segoe UI", 12),
                padx=10,
                pady=0
            )
            label2 = tk.Label(
                frame2,
                text=f"{desc}",
                anchor="w",
                bg="#2a2a2a",
                fg="#ccc",
                font=("Segoe UI", 8),
                padx=10,
                pady=2
            )

            label.pack(fill="x", padx=10, pady=2)
            label2.pack(fill="x", padx=10, pady=2)

        win.transient(app)
        win.grab_set()
        win.focus_force()

    def debug_key(key):
        print(f"[PLUGIN DEBUG] received key: {key}")

    tools.on_event("key_pressed", debug_key)
    tools.OnKeyPress("<Control-p>", lambda: print("[DEBUG] Ctrl+P bound"))
    tools.OnKeyPress("<Control-p>", show_plugin_manager)