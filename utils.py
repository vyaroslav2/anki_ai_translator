def get_selected_text_or_line():
    # We added console.log so you can see it in the Inspector (F12)
    return """
    (function() {
        var selection = window.getSelection();
        var text = "";
        
        if (selection.toString().length > 0) {
            text = selection.toString();
            console.log("AI Addon: Found selection: " + text);
        } else {
            // Fallback: Get the text of the current element/line
            text = selection.anchorNode ? selection.anchorNode.textContent : "";
            console.log("AI Addon: No selection, grabbing line: " + text);
        }
        return text;
    })()
    """