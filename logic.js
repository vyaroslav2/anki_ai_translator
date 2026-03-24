// logic.js
(function () {
  // Helper to pierce Anki's Shadow DOM
  function getActiveElement() {
    let activeEl = document.activeElement;
    while (
      activeEl &&
      activeEl.shadowRoot &&
      activeEl.shadowRoot.activeElement
    ) {
      activeEl = activeEl.shadowRoot.activeElement;
    }
    return activeEl;
  }

  window.ankiAI_getText = function () {
    const activeEl = getActiveElement();
    const rootNode = activeEl ? activeEl.getRootNode() : document;
    const sel = rootNode.getSelection
      ? rootNode.getSelection()
      : window.getSelection();

    if (!sel || !activeEl) {
      console.warn("AI Addon: No selection or active element.");
      return "";
    }

    let extractedText = sel.toString();

    // SCENARIO A: Text is manually highlighted
    if (extractedText.trim().length > 0) {
      console.log("AI Addon [JS]: Highlighted text ->", extractedText.trim());

      window.ankiAITargetRange = sel.getRangeAt(0).cloneRange();
      window.ankiAIWhitespacePrefix = ""; // No prefix needed for manual highlights

      return extractedText.trim();
    }

    // SCENARIO B: No text highlighted, grab the current line
    console.log("AI Addon [JS]: No text highlighted. Grabbing current line...");
    let anchor = sel.anchorNode;
    if (!anchor) return "";

    let blockElement = anchor.nodeType === 3 ? anchor.parentNode : anchor;
    while (
      blockElement &&
      blockElement !== activeEl &&
      !["DIV", "P", "LI"].includes(blockElement.nodeName)
    ) {
      blockElement = blockElement.parentNode;
    }

    if (!blockElement || blockElement === activeEl) {
      blockElement = activeEl;
    }

    extractedText = blockElement.innerText || blockElement.textContent || "";

    // --- NEW: CAPTURE LEADING INDENTATION ---
    // \s captures regular spaces and tabs, \u00A0 captures &nbsp;
    const leadingWhitespaceMatch = extractedText.match(/^[\s\u00A0]+/);
    window.ankiAIWhitespacePrefix = leadingWhitespaceMatch
      ? leadingWhitespaceMatch[0]
      : "";

    // Now trim the text so the AI gets a clean prompt
    extractedText = extractedText.trim();

    if (extractedText.length > 0) {
      console.log("AI Addon [JS]: Extracted line ->", extractedText);

      const range = document.createRange();
      range.selectNodeContents(blockElement);
      window.ankiAITargetRange = range;
    }

    return extractedText;
  };

  window.ankiAI_injectCloze = function (original, translated) {
    // Construct the cloze, PREPENDING the saved indentation
    const prefix = window.ankiAIWhitespacePrefix || "";
    const cloze = `${prefix}{{c1::${original}::${translated}}}`;

    const sel = window.getSelection();
    if (window.ankiAITargetRange) {
      sel.removeAllRanges();
      sel.addRange(window.ankiAITargetRange);
    }

    // --- NEW: OBLITERATE INLINE FORMATTING ---
    // This forcibly removes <i>, <b>, <u>, and font styling from the selection!
    document.execCommand("removeFormat", false, null);

    // Overwrite the selected line with our new, unformatted text
    document.execCommand("insertText", false, cloze);

    // Clean up
    window.ankiAITargetRange = null;
    window.ankiAIWhitespacePrefix = "";

    return true;
  };

  return "Logic Loaded";
})();
