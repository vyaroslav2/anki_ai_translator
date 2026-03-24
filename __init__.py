import re
import os
from aqt import mw
from aqt.editor import Editor
from aqt.gui_hooks import editor_did_init_shortcuts
from aqt.utils import tooltip

from .translation import translate_via_gemini
from .utils import get_js_logic

# --- SETUP DEBUG LOGGING ---
# This creates a debug.log file in the exact same folder as this __init__.py file
ADDON_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(ADDON_DIR, "debug.log")

def log_debug(step_name, text):
    """Writes the current state of the text to debug.log for easy troubleshooting."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{step_name}]\n{text}\n{'-'*40}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")

def on_translate_hotkey(editor: Editor):
    js_code = get_js_logic()
    editor.web.eval(js_code)

    def handle_text(selected_text):
        # 0. LOG INCOMING RAW TEXT
        log_debug("1. RAW TEXT FROM JS", f"'{selected_text}'")

        if not selected_text:
            tooltip("No text found. Please place your cursor on a line with text or highlight it.")
            return

        tooltip("Gemini is thinking...")

        # --- 1. PREPARE TEXT FOR AI ---
        ai_prompt_text = re.sub(r'\(.*?\)', '', selected_text)
        ai_prompt_text = re.sub(r'\s{2,}', ' ', ai_prompt_text).strip()
        log_debug("2. TEXT SENT TO AI", f"'{ai_prompt_text}'")

        def do_work():
            return translate_via_gemini(ai_prompt_text)

        def on_finished(future):
            try:
                translation = future.result()
                log_debug("3. RAW AI TRANSLATION", f"'{translation}'")

                if translation.startswith("Error"):
                    tooltip(translation)
                    return
                
                # --- 2. CLEAN UP ORIGINAL TEXT (For Anki Cloze) ---
                cloze_original = re.sub(r'["“”«»]', '', selected_text)
                cloze_original = re.sub(r"(?<!\w)['‘’]|['‘’](?!\w)", "", cloze_original)
                cloze_original = re.sub(r'\s{2,}', ' ', cloze_original).strip()
                log_debug("4. CLEANED ORIGINAL", f"'{cloze_original}'")

                # --- 3. CLEAN UP RUSSIAN TRANSLATION (For Anki Cloze) ---
                cloze_translation = re.sub(r'["“”«»]', '', translation)
                cloze_translation = re.sub(r"(?<!\w)['‘’]|['‘’](?!\w)", "", cloze_translation)
                cloze_translation = re.sub(r'(^|[.!?])\s*[\-—–]+\s*', r'\1 ', cloze_translation)
                cloze_translation = re.sub(r'\s{2,}', ' ', cloze_translation).strip()
                log_debug("5. CLEANED TRANSLATION", f"'{cloze_translation}'")

                # --- 4. INJECT CLOZE ---
                escaped_original = cloze_original.replace("`", "\\`").replace("${", "\\${")
                escaped_translation = cloze_translation.replace("`", "\\`").replace("${", "\\${")
                
                injection_call = f"window.ankiAI_injectCloze(`{escaped_original}`, `{escaped_translation}`)"
                editor.web.eval(injection_call)
                
                log_debug("6. INJECTION SUCCESS", f"Cloze: {{{{c1::{escaped_original}::{escaped_translation}}}}}")
                tooltip("Cloze generated!")

            except Exception as e:
                log_debug("ERROR", str(e))
                print(f"Callback Error: {e}")

        mw.taskman.run_in_background(do_work, on_finished)

    editor.web.evalWithCallback("window.ankiAI_getText()", handle_text)

def add_shortcuts(shortcuts, editor):
    shortcuts.append(("Ctrl+Shift+Alt+T", lambda: on_translate_hotkey(editor)))
    shortcuts.append(("F8", lambda: on_translate_hotkey(editor)))

editor_did_init_shortcuts.append(add_shortcuts)