(function () {
  window.ankiAI_getText = function () {
    const selection = window.getSelection();
    // Strictly grab highlighted text and trim it
    const rawText = selection.toString().trim();

    console.log("AI Addon [JS]: Highlighted text ->", rawText);
    return rawText;
  };

  window.ankiAI_injectCloze = function (original, translated) {
    const cloze = `{{c1::${original}::${translated}}}`;
    document.execCommand("insertText", false, cloze);
    return true;
  };

  return "Logic Loaded";
})();
