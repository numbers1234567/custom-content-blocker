
class RedditProc extends WebProc {
    className = "Post";
    baseRegEx     = new RegExp(".*://i\.redd\.it/*");
    previewRegEx  = new RegExp(".*://preview\.redd\.it/*");
    postLinkRegEx = new RegExp("/r/.*/comments/.*/.*/")
    getPostFromChildEl(el) {
        while (el && !el.className.split(" ").includes(this.className)) 
            el = el.parentElement;
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
            return "https://i.redd.it/" + filename;
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
        
    }
    getText(el) {
        return el.querySelector("div[data-adclicklocation=title]").children[0].textContent;
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
    getRelevantData(el) {
        el = this.getPostFromChildEl(el);
        return super.getRelevantData(el);
    }
    getDomUpdateData(mutationList) {
        var res = [];
        for (const mutation of mutationList) {
            for (const node of mutation.addedNodes) {
                let targetNode = node.firstChild.firstChild;
                res.push(this.getRelevantData(targetNode));
            }
        }
        return res;
    }
}