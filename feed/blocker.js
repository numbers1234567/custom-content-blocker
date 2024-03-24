import("./signals.js");

selecting_post = false;
var mouseEl = null;
var mouseElStyle = null;

// highlight the current e
function highlightMouseElement(e) {
    let newEl = document.elementFromPoint(e.clientX, e.clientY);
    if (newEl == mouseEl) return;
    // unhighlight
    if (mouseEl) 
        mouseEl.style = mouseElStyle;
    // highlight
    mouseEl = newEl;
    mouseElStyle = mouseEl.style;
    mouseEl.style.border = "3px solid red";
}

function blockEl(el) {
   if (el) element.style.backdropFilter = "blur(5px)";
}

function onEscPressed(e) {
    if (e.code=="escape") disableSelectionMode();
}

function onLMouse(e) {
    if (e.button==0) {
        console.log(mouseEl);
        blockEl(mouseEl);
        disableSelectionMode();
    }
}

function disableSelectionMode() {
    if (!selecting_post) return;
    // return to initial state
    selecting_post=false;
    document.removeEventListener("mousemove", highlightMouseElement);
    document.removeEventListener("keydown", onEscPressed);
    document.removeEventListener("mousedown", onLMouse);
    // unhighlight
    if (mouseEl) mouseEl.style = mouseElStyle;
    mouseEl = null;
    mouseElStyle = null;
}

function enableSelectionMode() {
    if (selecting_post) return;
    selecting_post = true;
    document.addEventListener("mousemove", highlightMouseElement);
    document.addEventListener("keydown", onEscPressed);
    document.addEventListener("mousedown", onLMouse);
}

browser.runtime.onMessage.addListener(
    request => {
        if (request.signal == Signal.BLOCK_MODE) enableSelectionMode();
    }
);