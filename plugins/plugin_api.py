import os, shutil, tkinter as tk
from typing import Literal
import shutil

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
    "key_pressed",
    "opened_context_menu"
]


class PluginAPI:
    def __init__(self, app, context):
        self.app = app
        self.context = context  # pass things like listb, errors, bg, fg, etc.
        self._event_handlers = {}

    def events(self):
        return dict(self._event_handlers)

    def get_module(self, name):
        try:
            importlib = self.modules["importlib"]
            return  importlib.import_module(name)
        except Exception as e:
            print(f"[PLUGIN] Could not load module {name}: {e}")


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
    
    def add_undo(self, action_dict):
        stack = self.context.get("undo_stack")
        if isinstance(stack, list):
            stack.append(action_dict)
            
    def register_undo_protoc(self,protocol,callback:callable):
        self.context.get("undo_protocols")[protocol] = callback
        
    def on_event(self, event_name:EventName, callback:callable):
        """Let plugins register a handler for a named event."""
        self._event_handlers.setdefault(event_name, []).append(callback)
        
    def run_in_thread(self, func, *args, **kwargs):
        threading = self.modules["threading"]
        t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        t.start()

    def OnKeyPress(self, key, callback:callable):
        def handle_key(key2):
            if key2 == key:
                callback()

        self.on_event("key_pressed", handle_key)
        
    def AddContextMenuCommand(self, label,command):
        CMC=self.context.get("CMC")
        CMC(label,command)

    def NewFilePrompt(self):
        CMC=self.context.get("CreateNewFilePrompt")
        CMC()

    def DeleteFilePrompt(self):
        CMC=self.context.get("DeleteFilePrompt")
        CMC()
        
    def RenameFilePrompt(self):
        CMC=self.context.get("RenameFilePrompt")
        CMC()

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
