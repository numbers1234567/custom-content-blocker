
class RedditProc extends WebProc {
    baseRegEx     = new RegExp(".*://i\.redd\.it/*");
    previewRegEx  = new RegExp(".*://preview\.redd\.it/*");
    postLinkRegEx = new RegExp("/r/.*/comments/.*/.*/")
    dataNode = document.getElementById("main-content").lastElementChild;
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
    getImgUrls(el) {
        let imgEls = el.getElementsByTagName("img");
        var imgLinks = []
        for (const imgEl of imgEls) {
            let imgLink = this.getImgFromPreviewURL(imgEl.src);
            if (imgLink)
                imgLinks.push(imgLink);
        }
        return imgLinks;
    }
    getVideoUrls(el) {
        return []
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
                if (node.tagName != "FACEPLATE-BATCH") continue;
                for (const node2 of node.children) { 
                    if (node2.tagName != "ARTICLE") continue;
                    res.push(this.getRelevantData(node2.getElementsByTagName("SHREDDIT-POST")[0]));
                }
            }
        }
        return res;
    }
}