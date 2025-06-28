plugin_info = {
    "name": "ExampleMod",
    "author": "MuZe",
    "version": "1.0.0",
    "description": "Sends Message About Plugin Loading?",
    "trusted": True
}


def on_load(app, tools):
    def on_start():
        tools.show_noti("Plugin loaded!")
    tools.on_event("app_start", on_start)