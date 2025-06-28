import os, shutil, tkinter as tk
from typing import Literal
import shutil
import PIL 
import vlc
import zipfile

EventName = Literal[
    "app_start",
    "app_exit",
    "plugins_loaded",
    "directory_changed",
    "file_selected",
    "file_deleted",
    "file_renamed",
    "file_created",
    "file_moved",
    "before_file_delete",
    "before_directory_change",
    "key_pressed"
]


class PluginAPI:
    def __init__(self, app, context):
        self.app = app
        self.context = context  # pass things like listb, errors, bg, fg, etc.
        self._event_handlers = {}

    def events(self):
        return dict(self._event_handlers)


    def show_noti(self, message, duration=3000, offset=(10, 10)):
        """Show Notification"""
        x = self.app.winfo_pointerx() + offset[0]
        y = self.app.winfo_pointery() + offset[1]

        toast = self.modules["tkinter"].Toplevel(self.app)
        toast.overrideredirect(True)
        toast.geometry(f"+{x}+{y}")
        toast.attributes("-topmost", True)

        label = tk.Label(toast, text=message, bg="#333", fg="#fff", font=("Segoe UI", 10), padx=10, pady=5)
        label.pack()

        # Auto-destroy after delay
        toast.after(duration, toast.destroy)



    def get_selected_filenames(self):
        sel = self.context["listb"].curselection()
        return [self.context["listb"].get(i) for i in sel]

    def delete_path(self, path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            print(f"[PLUGIN ERROR] Could not delete {path}: {e}")

    def run_error(self, message):
        RunError = self.context.get("RunError")
        if callable(RunError):
                try:
                    RunError(message)
                except Exception as e:
                    print(f"[ERROR] RunError failed: {e}")
        else:
            print("[WARNING] RunError not found or not callable.")
            
    def refreshlist(self):
        RefreshList = self.context.get("RefreshList")
        if callable(RefreshList):
                try:
                    RefreshList()
                except Exception as e:
                    print(f"[ERROR] RefreshList failed: {e}")
        else:
            print("[WARNING] RefreshList not found or not callable.")
            
    def GetCurrentPath(self):
        
        CPath=self.context.get("CurrentPath")
        return CPath()
            
    def on_event(self, event_name:EventName, callback:callable):
        """Let plugins register a handler for a named event."""
        self._event_handlers.setdefault(event_name, []).append(callback)
        
    def OnKeyPress(self, key, callback:callable):
        def handle_key(key2):
            if key2 == key:
                callback()

        self.on_event("key_pressed", handle_key)
        

    def trigger_event(self, event_name:EventName, *args, **kwargs):
        """Call all handlers associated with an event."""
        print(f"[DEBUG] Found {len(self._event_handlers.get(event_name, []))} handlers for '{event_name}'")
        for handler in self._event_handlers.get(event_name, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"[PLUGIN EVENT ERROR] {e}")
                
    @property
    
    def modules(self):
        return self.context["modules"]
