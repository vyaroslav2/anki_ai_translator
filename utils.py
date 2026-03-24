import os
from aqt import mw

def get_js_logic():
    """Reads logic.js from the addon folder to allow hot-reloading."""
    # Get the path to the addon folder
    addon_path = os.path.dirname(__file__)
    js_path = os.path.join(addon_path, "logic.js")
    
    try:
        with open(js_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading logic.js: {e}")
        return ""