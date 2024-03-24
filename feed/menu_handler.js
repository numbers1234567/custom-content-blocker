import("./signals.js");

// Basic handler for a menu which will signal events in content scripts.

browser.menus.create({
  id: "block_post",
  title: "Block post",
  contexts: ["all"],
});

// Send a message to tab to start
function on_block(info, tab) {
  browser.tabs.sendMessage(tab.id, {signal: Signal.BLOCK_MODE});
}

browser.menus.onClicked.addListener(
  (info, tab) => {
    if (info.menuItemId=="block_post") on_block(info, tab);
  }
);