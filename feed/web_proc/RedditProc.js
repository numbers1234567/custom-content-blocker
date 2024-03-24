import("./WebProc.js");

class RedditProc extends WebProc {
    className = "Post";
    getPostFromChildEl(el) {
        while (el.tagName != "html" && !el.className.split(" ").includes(this.className)) el = el.parentElement;
        if (el.tagName == "html") throw new InvalidPostError("Element is not part of a post.");
    }
    getImgFromPreviewURL(url) {
        return url;
    }
    getRelevantData(el) {
        getPostFromChildEl(el);
        // Get title
        let title = el.querySelector("div[data-adclicklocation=title]").textContent;
        // Get images
        let imgEls = el.getElementsByTagName("img");
        var imgLinks = []
        for (let imgEl in imgEls) 
            imgLinks.push(this.getImgFromPreviewURL(imgEl.src));
        // potentially getting other media here
        // ...
        
        return {text : title, media: imgLinks};
    }
}