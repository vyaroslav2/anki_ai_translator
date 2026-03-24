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
    window.ankiAI_activeElement = activeEl;

    const rootNode = activeEl ? activeEl.getRootNode() : document;
    const sel = rootNode.getSelection
      ? rootNode.getSelection()
      : window.getSelection();

    if (!sel || !activeEl) {
      console.warn("AI Addon: No selection or active element.");
      return "";
    }

    let extractedText = sel.toString();

    // SCENARIO: No text highlighted. Let's select the block/line containing the cursor.
    if (extractedText.trim().length === 0) {
      let anchor = sel.anchorNode;
      if (!anchor) return "";

      let blockElement = anchor.nodeType === 3 ? anchor.parentNode : anchor;
      while (
        blockElement &&
        blockElement !== activeEl &&
        !["DIV", "P", "LI", "ANKI-EDITABLE"].includes(
          blockElement.nodeName.toUpperCase(),
        )
      ) {
        blockElement = blockElement.parentNode;
      }

      if (!blockElement) blockElement = activeEl;

      const range = document.createRange();
      range.selectNodeContents(blockElement);
      sel.removeAllRanges();
      sel.addRange(range);

      extractedText = sel.toString();
    }

    if (extractedText.trim().length === 0) {
      console.warn("AI Addon: Line is empty.");
      return "";
    }

    // Capture indentation
    const leadingMatch = extractedText.match(/^[\s\u00A0]+/);
    const prefix = leadingMatch ? leadingMatch[0] : "";

    const trailingMatch = extractedText.match(/[\s\u00A0]+$/);
    const suffix = trailingMatch ? trailingMatch[0] : "";

    const cleanText = extractedText.trim();

    // Generate a unique token for the placeholder
    window.ankiAI_token = "[[AI_TRANSLATING_" + Date.now() + "]]";
    const skeleton = `${prefix}{{c1::${cleanText}::${window.ankiAI_token}}}${suffix}`;

    // IMMEDIATELY inject the skeleton while the window still has perfect focus
    document.execCommand("removeFormat", false, null);
    document.execCommand("insertText", false, skeleton);

    console.log("AI Addon: Placeholder injected immediately.");
    return cleanText;
  };

  window.ankiAI_injectCloze = function (original, translated) {
    const activeEl = window.ankiAI_activeElement;
    const token = window.ankiAI_token;

    if (!activeEl || !token) {
      console.warn("AI Addon [JS]: Missing active element or token.");
      return false;
    }

    // Surgical TextNode Replacement: We crawl the DOM looking for our token.
    // This doesn't use cursors or selections, so it works flawlessly even if the window is blurred.
    const root = activeEl.shadowRoot || activeEl;
    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      null,
      false,
    );

    let found = false;
    let node;
    while ((node = walker.nextNode())) {
      if (node.nodeValue.includes(token)) {
        // We found the exact node! Swap the token for the translation.
        node.nodeValue = node.nodeValue.replace(token, translated);
        found = true;
        break;
      }
    }

    // Failsafe: Just in case the TreeWalker missed it, do a raw HTML swap
    if (!found) {
      console.log(
        "AI Addon: TreeWalker missed token, using innerHTML fallback.",
      );
      root.innerHTML = root.innerHTML.replace(token, translated);
    }

    // Force Anki's ProseMirror engine to register the change and save the card
    activeEl.dispatchEvent(
      new Event("input", { bubbles: true, composed: true }),
    );

    // Clean up memory
    window.ankiAI_activeElement = null;
    window.ankiAI_token = null;

    console.log("AI Addon: Translation injected successfully.");
    return true;
  };

  return "Logic Loaded";
})();
