import traceback
from aqt import mw
from aqt.qt import *
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_init_shortcuts
from aqt.utils import showInfo, showText

from .translation import translate_via_gemini
from .utils import get_selected_text_or_line

def on_translate_hotkey(editor: Editor):
    print("Python: Hotkey triggered")
    
    def handle_text(text):
        try:
            if not text or not text.strip():
                showInfo("Python: No text received from JS.")
                return
            
            # We use a lambda to pass the text into the background worker
            def do_work():
                return translate_via_gemini(text)

            # In Anki, the 'on_done' function receives a 'Future' object
            def on_finished(future):
                try:
                    # This is where we extract the actual string result
                    result = future.result()
                    
                    showText(f"Gemini Result:\n{result}")
                    
                    if result and not result.startswith("Error"):
                        mw.app.clipboard().setText(result)
                        # Optional: provide a non-intrusive confirmation
                        mw.taskman.run_on_main(lambda: mw.tooltip("Copied to clipboard"))
                
                except Exception as e:
                    showText(f"Background Task Failed:\n{traceback.format_exc()}")

            mw.taskman.run_in_background(do_work, on_finished)
            
        except Exception as e:
            showText(f"Error in handle_text callback:\n{traceback.format_exc()}")

    # Trigger JS selection
    editor.web.evalWithCallback(get_selected_text_or_line(), handle_text)

def add_shortcuts(shortcuts, editor):
    shortcuts.append(("F8", lambda: on_translate_hotkey(editor)))
    shortcuts.append(("Ctrl+Shift+Alt+T", lambda: on_translate_hotkey(editor)))

editor_did_init_shortcuts.append(add_shortcuts)