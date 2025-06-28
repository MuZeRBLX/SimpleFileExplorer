plugin_info = {
    "name": "CreateNewFile Context Menu",
    "author": "MuZe",
    "version": "1.0.0",
    "description": 'Adds "Create New File" to Context Menu',
    "trusted": True
}


def on_load(app, tools):
    
    def on_start():
        tools.AddContextMenuCommand("Create New File", lambda e: tools.NewFilePrompt())
        
    tools.on_event("app_start", on_start)