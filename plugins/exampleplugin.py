plugin_info = {
    "name": "Plugin Loaded?",
    "author": "MuZe",
    "version": "1.0.0",
    "description": "Sends Message About Plugin Loading?",
    "trusted": True
}

def on_load(app, tools):
    
    os = tools.get_module("os")
    
    def on_start(items):
        for i in items:
            if not tools.get_file_properties(os.path.join(tools.GetCurrentPath(),i))["extension"] == "":
                tools.show_noti(str(tools.get_file_properties(os.path.join(tools.GetCurrentPath(),i))))
            
    tools.on_event("file_selected", on_start)