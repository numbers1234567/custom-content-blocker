
class RedditProc extends WebProc {
    className = "Post";
    getPostFromChildEl(el) {
        while (el && !el.className.split(" ").includes(this.className)) 
            el = el.parentElement;
        if (!el) throw new InvalidPostError("Element is not part of a post.");
        return el;
    }
    getImgFromPreviewURL(url) {
        // Returned form: https://i.redd.it/[filename]
        // list of matching expressions
        if (new RegExp(".*://i\.redd\.it/*").matches(url)) return url;
        if (new RegExp(".*://preview\.redd\.it/*").matches(url)) {
            let qName = url.split(".it/")[-1];
            let filename = qName.split("?")[0];
            return "https://i.redd.it/" + filename;
        }
        return null;
    }
    getRelevantData(el) {
        el = this.getPostFromChildEl(el);
        // Get title
        let title = el.querySelector("div[data-adclicklocation=title]").children[0].textContent;
        // Get images
        let imgEls = el.getElementsByTagName("img");
        var imgLinks = []
        for (const imgEl of imgEls) {
            let imgLink = this.getImgFromPreviewURL(imgEl.src);
            if (imgLink)
                imgLinks.push(imgLink);
        }
        // potentially getting other media here
        // ...

        return {text : title, media: {images: imgLinks}};
    }
}