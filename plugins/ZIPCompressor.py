plugin_info = {
    "name": "ZIP Compressor",
    "author": "PluginWizard",
    "version": "1.0",
    "description": "Compress selected files into a zip archive.",
    "trusted": True
}

def on_load(app, tools):
    print("🧩 [ZIP Compressor] Plugin loaded")

    os = tools.modules["os"]
    zipfile = tools.modules["zipfile"]

    api = tools

    def compress_selected2():
        selected = api.get_selected_filenames()
        if not selected:
            api.run_error("No files selected to compress.")
            return

        current_dir = api.GetCurrentPath()
        archive_path = os.path.join(current_dir, "compressed.zip")

        try:
            with zipfile.ZipFile(archive_path, 'w') as zipf:
                for fname in selected:
                    full_path = os.path.join(current_dir, fname)
                    if os.path.isfile(full_path):
                        zipf.write(full_path, arcname=fname)
                    else:
                        api.run_error(f"Skipping '{fname}': Not a file.")

            api.add_undo({
                "action": "compress_file",
                "info": {"archive_path": archive_path}
            })

            api.refreshlist()
            api.show_noti("✅ Created compressed.zip")

        except Exception as e:
            api.run_error(f"Compression failed: {e}")
            
    def compress_selected():
        
        tools.run_in_thread(compress_selected2)

    def undo_zip_compress(info):
        archive_path = info.get("archive_path")
        if archive_path and os.path.exists(archive_path):
            try:
                os.remove(archive_path)
                api.refreshlist()
                print(f"[UNDO] Deleted: {archive_path}")
            except Exception as e:
                api.run_error(f"Undo failed: {e}")
        else:
            api.run_error("Undo failed: ZIP file not found.")

    api.register_undo_protoc("compress_file", undo_zip_compress)
    api.AddContextMenuCommand("📦 Compress to ZIP (undoable)", compress_selected)