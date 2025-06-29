import tkinter as tk
import os
import subprocess
import shutil
import PIL
from PIL import Image, ImageTk
import vlc  # pip install python-vlc
import zipfile
import importlib
import plugins.plugin_api
from plugins.plugin_api import PluginAPI
import tkinter.messagebox as messagebox
import random
import json
import threading


# Theme colors
bg  = "#1b1b1b"
bg2 = "#111111"
fg  = "#ffffff"

showhidden = False
errors = []
undo_stack = []
CurrentTree  = "C:\\"
# File‐type lists
WRITABLELIST = ["txt", "md", "rtf", "html", "py", "log","ini"]
IMAGELIST    = ["jpg", "png", "gif"]
VIDEOLIST    = ["mp4", "avi", "mkv", "mov", "flv", "wmv", "webm", "mpeg", "mpg","mp3","wav"]
undo_protocols = {}

# Plugins

PLUGINS = []

def CreateNewFile():
    WRITABLELIST = ["txt", "md", "rtf", "html", "py", "log", "ini"]
    IMAGELIST = ["jpg", "png", "gif"]
    VIDEOLIST = ["mp4", "avi", "mkv", "mov", "flv", "wmv", "webm", "mpeg", "mpg", "mp3", "wav"]

    win = tk.Toplevel(bg=bg)
    win.title("Create New File or Folder")

    inp = tk.Entry(win, bg=bg2, fg=fg)
    inp.pack(side="top")

    def Create():
        filename = inp.get().strip()
        if not filename:
            RunError("ERROR 1: FILE/FOLDER NAME CANNOT BE EMPTY.")
            return

        full_path = os.path.join(CurrentTree, filename)

        if os.path.exists(full_path):
            RunError("ERROR 2: FILE OR FOLDER ALREADY EXISTS.")
            return

        ext = filename.split(".")[-1].lower() if "." in filename else ""
        try:
            if ext in WRITABLELIST + IMAGELIST + VIDEOLIST:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("")  # empty file
                action_type = "create"
            else:
                os.makedirs(full_path)
                action_type = "mkdir"

            undo_stack.append({
                "action": action_type,
                "path": full_path
            })
            RefreshList()
            win.destroy()
        except Exception as e:
            RunError(f"ERROR 3: COULD NOT CREATE FILE OR FOLDER.\n{e}")

    But = tk.Button(win, bg=bg2, fg=fg, text="Create", command=Create)
    But.pack(side="top")

def getpath():
    
    return CurrentTree

def on_list_select_event(event):
    selection = listb.curselection()
    if not selection:
        return

    selected_items = [listb.get(i) for i in selection]
    if hasattr(API, "trigger_event"):
        API.trigger_event("file_selected", selected_items)

import importlib.util
import os

def load_plugins(root, context, path="plugins", trust_registry_path="data.json"):
    plugins = []

    # Load trust list (or create if missing)
    if os.path.exists(trust_registry_path):
        with open(trust_registry_path, "r") as f:
            data = json.load(f)
            trusted_plugins = data["Plugins"]
    else:
        trusted_plugins = []

    for file in os.listdir(path):
        if file.endswith(".py") and file not in ("__init__.py", "plugin_api.py"):
            full_path = os.path.join(path, file)
            name = os.path.splitext(file)[0]

            # Check if plugin is trusted
            if file not in trusted_plugins:
                response = tk.messagebox.askyesno(
                    "Trust Plugin?",
                    f"The plugin '{file}' is untrusted.\nDo you want to allow it?"
                )
                if response:
                    trusted_plugins.append(file)
                    with open(trust_registry_path, "w") as f:
                        json.dump({"Plugins":trusted_plugins}, f, indent=4)
                else:
                    print(f"[PLUGIN BLOCKED] {file} was not trusted.")
                    continue

            spec = importlib.util.spec_from_file_location(name, full_path)
            mod = importlib.util.module_from_spec(spec)

            try:
                spec.loader.exec_module(mod)

                info = getattr(mod, "plugin_info", {
                    "name": name,
                    "author": "Unknown",
                    "version": "0.0",
                    "trusted": True
                })

                print(f"[PLUGIN LOADED] {info['name']} by {info['author']} (v{info['version']})")
                mod._info = info
                plugins.append(mod)

                if hasattr(mod, "on_load"):
                    mod.on_load(root, API)

            except Exception as e:
                RunError(f"[PLUGIN ERROR] Failed to load {file}: {e}")

    context["plugins_loaded"] = plugins
    return plugins


                
#–– Basic Actions (Errors, Ctrl + Z, Refresh Viewer) ––#

def ToggleHidden(event=None):
    
    global showhidden
    showhidden = not showhidden
    RefreshList()

def safe_move_to_Folder(original_path, new_folder):
    filename = os.path.basename(original_path)
    name, ext = os.path.splitext(filename)

    i = 1
    candidate = filename
    while os.path.exists(os.path.join(new_folder, candidate)):
        suffix = f" ({i})"
        candidate = f"{name}{suffix}{ext}"
        i += 1

    os.rename(original_path, os.path.join(new_folder, candidate))
    return os.path.join(new_folder, candidate)

def RunError(Error="ERROR 1: EXAMPLEERROR"):
    win = tk.Toplevel(bg=bg)
    win.title(f"ERROR: {Error}")
    
    global errors
            
    def End():
        for i in errors:
            p= errors.pop()
            
            p.destroy()
            
        
            
    inp = tk.Label(win,bg=bg2,fg=fg,text=Error)
    inp.pack(side="top")
    errors.append(win)
    But = tk.Button(win,bg=bg2,fg=fg,command=End,text="Accept")
    But.pack(side="top")
    
    win.bind("<Return>", lambda e: End())

def undo_last_action(event=None):
    if not undo_stack:
        RunError("ERROR 0: Undo Failed (No Things To Undo.)")
        return

    last = undo_stack.pop()
    try:
        if last["action"] == "rename":
            os.rename(last["new"], last["old"])
        elif last["action"] == "delete":
            os.rename(last["trashed"], last["original"])
        elif last["action"] == "move":
            os.rename(last["new"], last["old"])
        elif last["action"] == "deletemultiple":
            for entry in last["Trashed"]:
                os.rename(entry["trashed"], entry["original"])
        elif last["action"] == "duplicate":
            # Delete the duplicate copy
            if os.path.isdir(last["copy"]):
                shutil.rmtree(last["copy"])
            else:
                os.remove(last["copy"])
        elif last["action"] == "create":
            if os.path.isdir(last["path"]):
                shutil.rmtree(last["path"])
            else:
                os.remove(last["path"])
        else:
            action = last.get("action")
            info = last.get("info", {})  # optional details passed by plugin
            handler = context.get("undo_protocols", {}).get(action)

            if callable(handler):
                try:
                    handler(info)
                except Exception as e:
                    RunError(f"Undo Failed: {e}")
            else:
                RunError(f"Undo Failed: Unknown action '{action}'")




        RefreshList()

    except Exception as e:
        RunError("ERROR 0: Undo Failed due to error in code (Easter Egg?)")

def RefreshList():
    
            listb.delete(0, tk.END)
            listx.delete(0, tk.END)
            listb.insert(tk.END, "..")
            for item in DisplayTree(CurrentTree):
                
                if not item.startswith(".") and not item.startswith("$") or showhidden == True:
                
                    if "." in item and item.split(".")[0]:
                        listx.insert(tk.END, item)
                    
                    listb.insert(tk.END, item)
                    
def CleanOldTrash():
    trash_path = os.path.join(CurrentTree, ".trash")  # or wherever your trash folder lives

    if not os.path.isdir(trash_path):
        return

    for item in os.listdir(trash_path):
        item_path = os.path.join(trash_path, item)

        try:


            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            print(f"⚠️ Couldn’t delete {item}: {e}")

    
#–– File Actions ––#
    
def DeleteFile():
    sel = listb.curselection()
    if not sel:
        return
    if listb.get(sel[0]) == "..":
        return

    if len(sel) > 1:

        # Build prompt window
        win = tk.Toplevel(bg=bg)
        win.title(f"Delete Files?")

        lbl = tk.Label(win, text=f"Are you sure you want to delete these files?", bg=bg, fg=fg)
        lbl.pack(padx=10, pady=10)

        selected_items = [listb.get(i) for i in sel]

        itemstrashed = []

        def ConfirmDelete():
            try:
                for i in selected_items:
                        
                    FileName = str(i)
                    full_path = os.path.join(CurrentTree, FileName)
                    
                    trash = os.path.join(CurrentTree, ".trash")
                    os.makedirs(trash, exist_ok=True)

                    trashed_path = safe_move_to_Folder(full_path,trash)

                    itemstrashed.append({                        
                        "original": full_path,
                        "trashed": trashed_path
                        })

                    RefreshList()
                    
                undo_stack.append({
                        "action": "deletemultiple",
                        "Trashed": itemstrashed
                    })
                win.destroy()
            except Exception as e:
                RunError(f"ERROR 4: {str(e)}")

        tk.Button(win, text="Delete", command=ConfirmDelete, bg=bg2, fg=fg).pack(pady=(0, 10))
        
    else:
    
     # Build prompt window
        win = tk.Toplevel(bg=bg)
        win.title(f"Delete Files?")

        lbl = tk.Label(win, text=f"Are you sure you want to delete these files?", bg=bg, fg=fg)
        lbl.pack(padx=10, pady=10)

        def ConfirmDelete():
            try:
                        
                FileName = str(listb.get(sel[0]))
                full_path = os.path.join(CurrentTree, FileName)
                    
                trash = os.path.join(CurrentTree, ".trash")
                os.makedirs(trash, exist_ok=True)

                trashed_path = safe_move_to_Folder(full_path,trash)

                undo_stack.append({
                        "action": "delete",
                        "original": full_path,
                        "trashed": trashed_path
                })

                RefreshList()
                win.destroy()
            except Exception as e:
                RunError(f"ERROR 4: {str(e)}")

        tk.Button(win, text="Delete", command=ConfirmDelete, bg=bg2, fg=fg).pack(pady=(0, 10))

def RenameFile():
    
    sel = listb.curselection()
    if not sel:
        return
    if listb.get(sel[0]) == "..":
        return
    
    win = tk.Toplevel(bg=bg)
    FileNameOrig = str(listb.get(sel[0]))
    win.title(f"Rename {FileNameOrig}")
            
    inp = tk.Entry(win,bg=bg2,fg=fg)
    inp.pack(side="top")
            
    def Rename():
                
        if inp.get():
                    
            if FileNameOrig.count(".")==1 and inp.get().count(".")==0:
                
                newname = (f"{inp.get()}.{FileNameOrig.split('.')[1]}")
                
                os.rename(os.path.join(CurrentTree,FileNameOrig),os.path.join(CurrentTree,newname))
                undo_stack.append({
                "action": "rename",
                "old": os.path.join(CurrentTree, FileNameOrig),
                "new": os.path.join(CurrentTree, newname)
                })
                RefreshList()
                win.destroy()
                
                return
            
            if FileNameOrig.count(".")==0 and inp.get().count(".")==0:
                
                newname = (f"{inp.get()}")
                
                os.rename(os.path.join(CurrentTree,FileNameOrig),os.path.join(CurrentTree,newname))
                undo_stack.append({
                "action": "rename",
                "old": os.path.join(CurrentTree, FileNameOrig),
                "new": os.path.join(CurrentTree, newname)
                })
                RefreshList()
                win.destroy()
                
                return
            
            else:
                
                RunError("ERROR 2: INVALID NAME OR FILE (CANNOT CONTAIN MULTIPLE .'s, AND NO .'s CAN BE IN YOUR NEW FILE NAME.)")
                
    But = tk.Button(win,bg=bg2,fg=fg,text="Rename",command=Rename)
    But.pack(side="top")
                
def DuplicateFile():
    sel = listb.curselection()
    if not sel:
        return
    if listb.get(sel[0]) == "..":
        return

    FileNameOrig = str(listb.get(sel[0]))
    FullPath = os.path.join(CurrentTree, FileNameOrig)

    folder, name = os.path.split(FullPath)
    base, ext = os.path.splitext(name)

    # Generate new name
    i = 1
    while True:
        suffix = f" (copy)" if i == 1 else f" (copy {i})"
        new_name = f"{base}{suffix}{ext}"
        new_path = os.path.join(folder, new_name)
        if not os.path.exists(new_path):
            break
        i += 1

    try:
        if os.path.isdir(FullPath):
            shutil.copytree(FullPath, new_path)
        else:
            shutil.copy2(FullPath, new_path)

        undo_stack.append({
            "action": "duplicate",
            "original": FullPath,
            "copy": new_path
        })
        
        API.trigger_event("file_created",new_path)

        RefreshList()

    except Exception as e:
        RunError(f"ERROR 5: DUPLICATION FAILED – {str(e)}")      
                    
def MoveFile():
    sel = listb.curselection()
    if not sel:
        return
    if listb.get(sel[0]) == "..":
        return
    Tree = CurrentTree
    sel = sel
    
    win = tk.Toplevel(bg=bg)
    FileNameOrig = str(listb.get(sel[0]))
    win.title(f"Move {FileNameOrig}")
            
    def Move():
        newtree = CurrentTree
        
        undo_stack.append({
            "action": "move",
            "old": os.path.join(Tree, FileNameOrig),
            "new": os.path.join(newtree, FileNameOrig)
            })
        
        os.rename(os.path.join(Tree,FileNameOrig),os.path.join(newtree,FileNameOrig))
        RefreshList()
        API.trigger_event("file_moved",os.path.join(newtree, FileNameOrig))
        win.destroy()

    But = tk.Button(win,bg=bg2,fg=fg,text="Finish Move",command=Move)
    But.pack(side="top")
                
def FindSelect():
    sel = listx.curselection()
    if not sel:
        return
    txt = listx.get(sel[0])
    for i, v in enumerate(listb.get(0, tk.END)):
        if v == txt:
            listb.select_set(i)

def DisplayTree(path):
    global CurrentTree
    if os.path.exists(path):
        CurrentTree = path
        return os.listdir(path)
    return ["ERROR"]

#–– File Viewers ––#

def OpenTextReader(content, title):
    win = tk.Toplevel(bg=bg)
    win.title(f"{title} (READ-ONLY)")
    w, h = win.winfo_screenwidth()-50, win.winfo_screenheight()-50
    win.maxsize(w, h)

    text = tk.Text(
        win, bg=bg, fg=fg,
        insertbackground=fg,
        wrap="word"
    )
    text.insert("1.0", content)
    text.pack(fill="both", expand=True, padx=5, pady=5)

    scroll = tk.Scrollbar(win, command=text.yview, troughcolor=bg2)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")


def OpenImageDisplay(filepath):
    win = tk.Toplevel(bg=bg)
    win.title(f"{os.path.basename(filepath)} (IMAGE)")
    w, h = win.winfo_screenwidth()-50, win.winfo_screenheight()-50
    win.maxsize(w, h)

    img_orig = Image.open(filepath)
    zoom = 1.0

    display = ImageTk.PhotoImage(img_orig)
    lbl = tk.Label(win, image=display, bg=bg)
    lbl.image = display
    lbl.pack(expand=True)

    def do_zoom(e):
        nonlocal zoom
        zoom *= 1.1 if e.delta > 0 else 1/1.1
        new_size = (
            int(img_orig.width * zoom),
            int(img_orig.height * zoom)
        )
        resized = img_orig.resize(new_size, Image.Resampling.LANCZOS)
        pic = ImageTk.PhotoImage(resized)
        lbl.configure(image=pic)
        lbl.image = pic

    win.bind("<MouseWheel>", do_zoom)
    win.bind("<Button-4>", do_zoom)
    win.bind("<Button-5>", do_zoom)


def OpenVideoPlayer(filepath):
    win = tk.Toplevel(bg=bg)
    win.title(f"{os.path.basename(filepath)} (VIDEO)")
    w, h = win.winfo_screenwidth()-50, win.winfo_screenheight()-50
    win.maxsize(w, h)
    win.geometry("800x600")

    # VLC setup
    instance = vlc.Instance()
    player   = instance.media_player_new()
    media    = instance.media_new(filepath)
    player.set_media(media)

    # Video frame
    vf = tk.Frame(win, bg=bg2)
    vf.pack(fill="both", expand=True)
    win.update_idletasks()
    player.set_hwnd(vf.winfo_id())  # Windows

    player.play()

    # Scrub bar
    progress = tk.DoubleVar()
    scrubbing = [False]

    def update_progress():
        if player.get_length() > 0 and not scrubbing[0]:
            pos = player.get_time() / player.get_length() * 100
            progress.set(pos)
        win.after(500, update_progress)

    def on_scrub(val):
        if player.get_length() > 0:
            t = float(val) / 100 * player.get_length()
            player.set_time(int(t))

    def start_scrub(e):
        scrubbing[0] = True

    def end_scrub(e):
        scrubbing[0] = False
        on_scrub(progress.get())

    slider = tk.Scale(
        win, variable=progress,
        from_=0, to=100, orient="horizontal",
        showvalue=0, command=on_scrub,
        bg=bg, fg=fg,
        troughcolor=bg2, highlightbackground=bg
    )
    slider.bind("<ButtonPress-1>", start_scrub)
    slider.bind("<ButtonRelease-1>", end_scrub)
    slider.pack(fill="x", padx=5, pady=5)

    # Controls
    ctrl = tk.Frame(win, bg=bg)
    ctrl.pack(pady=5)

    tk.Button(
        ctrl, text="▶ Play", command=player.play,
        bg=bg2, fg=fg, activebackground=bg, activeforeground=fg
    ).pack(side="left", padx=5)
    tk.Button(
        ctrl, text="⏸ Pause", command=player.pause,
        bg=bg2, fg=fg, activebackground=bg, activeforeground=fg
    ).pack(side="left", padx=5)
    tk.Button(
        ctrl, text="⏹ Stop", command=player.stop,
        bg=bg2, fg=fg, activebackground=bg, activeforeground=fg
    ).pack(side="left", padx=5)
    tk.Button(
        ctrl, text="🔉 Mute", command=player.audio_toggle_mute,
        bg=bg2, fg=fg, activebackground=bg, activeforeground=fg
    ).pack(side="left", padx=5)

    # Volume slider
    vol = tk.IntVar(value=100)
    def on_vol(v): 
        
        if int(v) > 100:
            
            vs.configure(fg="#a80000")
            
        else:
        
            vs.configure(fg=fg)
        
        player.audio_set_volume(int(v))

    vs = tk.Scale(
        win, from_=0, to=200,
        orient="horizontal", label="Volume (IF RED, BOOSTER IS ON)",
        variable=vol, command=on_vol,
        bg=bg, fg=fg,
        troughcolor=bg2, highlightbackground=bg
    )
    vs.pack(fill="x", padx=5)

    # Cleanup on close
    def on_close():
        player.stop()
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
    update_progress()

def on_item_select():
    global CurrentTree

    sel = listb.curselection()
    if sel:
        
        if len(sel) == 1:
        
            selected_text = str(listb.get(sel[0]))

            # Handle ".." navigation
            if selected_text == "..":
                newpath = os.path.dirname(CurrentTree)
            else:
                if "." in selected_text and not selected_text.startswith("."):
                    exname = selected_text.split(".")[-1].lower()
                    full_path = os.path.join(CurrentTree, selected_text)

                    if exname == "exe":
                        subprocess.run(full_path)
                    elif exname in WRITABLELIST:
                        
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                        except PermissionError:
                            RunError("ERROR 3: YOU CANNOT OPEN RESTRICTED FILES. TRY RUNNING AS ADMINISTRATOR?")
                        OpenTextReader(content, selected_text)
                    elif exname in IMAGELIST:
                        OpenImageDisplay(full_path)
                    elif exname in VIDEOLIST:
                        OpenVideoPlayer(full_path)
                    return

                # Enter folder
                if not selected_text == ".trash":
                    newpath = os.path.join(CurrentTree, selected_text)
                else:
                    RunError("ERROR 3: YOU CANNOT OPEN RESTRICTED FILES. THIS FILE IS A SIMPLE FILE EXPLORER FILE.")
                    return

            if os.path.isdir(newpath):
                CurrentTree = newpath
                listb.delete(0, tk.END)
                listx.delete(0, tk.END)
                listb.insert(tk.END, "..")
                API.trigger_event("directory_changed",CurrentTree)
                try:
                    os.listdir(CurrentTree)

                    for item in os.listdir(CurrentTree):
                        if not item.startswith(".") and not item.startswith("$") or showhidden == True:
                            if "." in item and item.split(".")[0]:
                                listx.insert(tk.END, item)
                            listb.insert(tk.END, item)
                except PermissionError:
                    RunError("ERROR 3: YOU CANNOT OPEN RESTRICTED FILES. TRY RUNNING AS ADMINISTRATOR?")
                    
        else:
            
            for v in sel:
                
                selected_text = str(listb.get(v))

                # Handle ".." navigation

                if "." in selected_text:
                    exname = selected_text.split(".")[-1].lower()
                    full_path = os.path.join(CurrentTree, selected_text)
                    if exname == "exe":
                        subprocess.run(full_path)
                        return
                    elif exname in WRITABLELIST:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        OpenTextReader(content, selected_text)
                    elif exname in IMAGELIST:
                        OpenImageDisplay(full_path)
                    elif exname in VIDEOLIST:
                        root.after(100, lambda path=full_path: OpenVideoPlayer(path))

            

#–– Main App ––#

root = tk.Tk()
root.config(bg=bg)
root.title("Simple File Explorer")
w, h = root.winfo_screenwidth()-50, root.winfo_screenheight()-50
root.maxsize(w, h)

listb = tk.Listbox(
    root, selectmode=tk.EXTENDED,
    width=100, height=40,
    bg=bg, fg=fg,
    selectbackground="#333333",
    highlightbackground=bg
)
listb.pack(padx=10, pady=10, side="left")

listx = tk.Listbox(
    root, selectmode=tk.SINGLE,
    width=100, height=40,
    bg=bg, fg=fg,
    selectbackground="#333333",
    highlightbackground=bg
)
listx.pack(padx=10, pady=10, side="right")

btn = tk.Button(
    root, text="Open Path (Enter)", command=lambda: on_item_select(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn.pack(pady=1, side="bottom")
btn2 = tk.Button(
    root, text="Delete (Delete)", command=lambda: DeleteFile(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn2.pack(pady=1, side="bottom")
btn3 = tk.Button(
    root, text="Move (F3)", command=lambda: MoveFile(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn3.pack(pady=1, side="bottom")
btn4 = tk.Button(
    root, text="Rename (F2)", command=lambda: RenameFile(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn4.pack(pady=1, side="bottom")
btn5 = tk.Button(
    root, text="Undo (CTRL+Z)", command=lambda: undo_last_action(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn5.pack(pady=1, side="bottom")
btn6 = tk.Button(
    root, text="Duplicate (CTRL+D)", command=lambda: DuplicateFile(),
    bg=bg2, fg=fg,
    activebackground=bg, activeforeground=fg
)
btn6.pack(pady=1, side="bottom")

context_menu = tk.Menu(root, tearoff=0, bg=bg2, fg=fg)

def AddContextMenuCommand(label,commande):
    context_menu.add_command(label=label, command=commande)

context_menu.add_command(label="Open", command=on_item_select)
context_menu.add_command(label="Rename", command=RenameFile)
context_menu.add_command(label="Duplicate", command=DuplicateFile)
context_menu.add_command(label="Delete", command=DeleteFile)
context_menu.add_command(label="Move", command=MoveFile)

def show_context_menu(event):
    # Select the item under the cursor
    API.trigger_event("opened_context_menu")
    try:
        listb.selection_clear(0, tk.END)
        listb.selection_set(listb.nearest(event.y))
    except:
        pass

    context_menu.tk_popup(event.x_root, event.y_root)

modules = {"tkinter":tk,"os":os,"shutil":shutil,"vlc":vlc,"PIL":PIL,"zipfile":zipfile,"random":random,"threading":threading,"importlib":importlib}

context = {
    "listb": listb,
    "RunError": RunError,
    "bg": bg,
    "fg": fg,
    "errors": errors,
    "CurrentPath": getpath,
    "RefreshList": RefreshList,
    "CMC":AddContextMenuCommand,
    "CreateNewFilePrompt":CreateNewFile,
    "RenameFilePrompt":RenameFile,
    "DeleteFilePrompt":DeleteFile,
    "modules":modules,
    "undo_stack":undo_stack,
    "undo_protocols":undo_protocols
}

API = PluginAPI(root,context=context)

listb.bind("<Button-3>", show_context_menu)

def handle_return(e):
    on_item_select()
    API.trigger_event("key_pressed", "Return")

def handle_home(e):
    FindSelect()
    API.trigger_event("key_pressed", "Home")

def handle_f2(e):
    RenameFile()
    API.trigger_event("key_pressed", "F2")

def handle_Del(e):
    DeleteFile()
    API.trigger_event("key_pressed", "Delete")
    
def handle_f3(e):
    MoveFile()
    API.trigger_event("key_pressed", "F3")

root.bind("<Return>", handle_return)
root.bind("<Home>",   handle_home)
root.bind("<F2>",     handle_f2)
root.bind("<F3>",     handle_f3)

def DeleteKeyHandler(event):
    if event.state & 0x4:  # Control is held
        print("Ctrl+Delete detected — ignoring.")
        return
    DeleteFile()

def Exit():
    API.trigger_event("app_exit")
    CleanOldTrash()
    root.destroy()

def KeyTrigger(event):
    key = event.keysym.lower()

    # Modifier flags (platform-sensitive)
    is_shift = event.state & 0x0001
    is_ctrl = event.state & 0x0004
    is_alt = event.state & 0x20000  # ← more reliable on some Windows builds

    mods = []
    if is_ctrl: mods.append("Control")
    if is_alt: mods.append("Alt")
    if is_shift: mods.append("Shift")

    if key not in ["alt_l", "alt_r", "control_l", "control_r", "shift_l", "shift_r"]:
        combo = f"<{'-'.join(mods)}-{key}>" if mods else key
        print(f"[DEBUG] state: {event.state}, combo: {combo}")
        API.trigger_event("key_pressed", combo)


root.bind("<Key>", KeyTrigger)
root.bind("<Delete>", handle_Del)
root.bind("<Control-Delete>")
root.bind("<Control-z>", undo_last_action)
root.bind("<Control-d>", lambda e: DuplicateFile())
root.bind("<Control-n>", lambda e: CreateNewFile())
root.bind("<Control-Shift-Q>", ToggleHidden)
root.bind("<Control-Shift-q>", ToggleHidden)
listb.bind("<<ListboxSelect>>", on_list_select_event)

# Load Plugins and Contexts

plugins = load_plugins(root, context)
# Initial directory load
RefreshList()
API.trigger_event("app_start")

root.protocol("WM_DELETE_WINDOW", Exit)

root.mainloop()
