// Define dom observer
function onDomUpdate(mutationList, observer) {
    const newPosts = proc.getDomUpdateData(mutationList);
    for (const post of newPosts) {
        post["data"].then((data) => {
            processPost(data, () => {blockEl(post["post"]); console.log(post["post"])});
        });
    }
}

const changeObserverConfig = {childList : true};
const observer = new MutationObserver(onDomUpdate);

observer.observe(proc.getDataNode(), changeObserverConfig);

// manual blocking
var selecting_post = false;
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
    if (newEl) {
        mouseEl = newEl;
        mouseElStyle = mouseEl.style;
        mouseEl.style.border = "3px solid red";
    }
}

function blockEl(el) {
   if (el) el.style.visibility = "hidden";
}

function onEscPressed(e) {
    if (e.code=="Escape") disableSelectionMode();
}

function onLMouse(e) {
    if (e.button==0) {
        let toBlock = proc.getPostFromChildEl(mouseEl);
        // Prevent click from propagating
        e.stopPropagation();
        e.preventDefault();
        disableSelectionMode();
        // [TO-DO] send element to backend for processing.
        blockEl(toBlock);
    }
}

function disableSelectionMode() {
    if (!selecting_post) return;
    // return to initial state
    selecting_post=false;
    document.removeEventListener("mousemove", highlightMouseElement);
    document.removeEventListener("keydown", onEscPressed);
    document.removeEventListener("click", onLMouse);
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
    document.addEventListener("click", onLMouse, true);
}

browser.runtime.onMessage.addListener(
    request => {
        if (request.signal == Signal.BLOCK_MODE) enableSelectionMode();
    }
);