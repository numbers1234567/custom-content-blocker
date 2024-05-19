function redditGetDataNode() {
    let cur = document.getElementById("main-content").lastElementChild;
    if (cur.tagName=="DSA-TRANSPARENCY-MODAL-PROVIDER")  // on all or popular
        cur = cur.lastElementChild
    console.log(cur);
    return cur;
}

class RedditProc extends WebProc {
    baseRegEx     = new RegExp(".*://i\.redd\.it/*");
    previewRegEx  = new RegExp(".*://preview\.redd\.it/*");
    postLinkRegEx = new RegExp("/r/.*/comments/.*/.*/")
    dataNode = redditGetDataNode();
    getPostFromChildEl(el) {
        while (el && el.tagName!="SHREDDIT-POST") {
            el = el.parentElement;
        }
        if (!el) throw new InvalidPostError("Element is not part of a post.");
        return el;
    }
    getImgFromPreviewURL(url) {
        // Returned form: https://i.redd.it/[filename]
        // list of matching expressions
        if (this.baseRegEx.test(url)) return url;
        if (this.previewRegEx.test(url)) {
            let qName = url.split("it/")[1];
            let filename = qName.split("?")[0];
            //return "https://i.redd.it/" + filename;
        }
        return null;
    }
    getImgData(el) {
        let imgEls = Array.from(el.querySelectorAll("img.media-lightbox-img"));
        
        return imgEls.map(getRawPixelData);
    }
    getVidData(el) { // There may actually be no way to get the raw video data, so this will just get a frame.
        const player = el.getElementsByTagName("SHREDDIT-PLAYER")[0];
        if (!player) return [];
        const playerRoot = player && player.shadowRoot;
        const vidEls = Array.from(playerRoot.childNodes[2].getElementsByTagName("video"));
        return vidEls.map(getRawPixelData);
    }
    getText(el) {
        return el.querySelectorAll('[slot="title"]')[0].textContent;
    }
    getID(el) {
        let anchors = el.getElementsByTagName("a");
        for (const anchor of anchors) {
            let link = anchor.getAttribute("href");
            if (this.postLinkRegEx.test(link))
                return link.replace("/comments", "").replaceAll("/", "_");
        }
        return null;
    }
    getDataNode() {
        return this.dataNode;
    }
    getDomUpdateData(mutationList) {
        var res = [];
        for (const mutation of mutationList) {
            for (const node of mutation.addedNodes) {
                if (node.tagName == "ARTICLE") 
                    res.push({"data" : this.getRelevantData(node.getElementsByTagName("SHREDDIT-POST")[0]), "post" : node});
                if (node.tagName != "FACEPLATE-BATCH") continue;
                for (const node2 of node.children) { 
                    if (node2.tagName != "ARTICLE") continue;
                    res.push({"data" : this.getRelevantData(node2.getElementsByTagName("SHREDDIT-POST")[0]), "post" : node});
                }
            }
        }
        return res;
    }
}