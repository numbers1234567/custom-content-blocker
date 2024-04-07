class InvalidPostError extends Error {};
class WebProcUndefinedError extends Error {};

class WebProc {
    getPostFromChildEl(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getImgUrls(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getVideoUrls(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getText(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getID(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getRelevantData(el) {
        return {media: {text: this.getText(el), images: this.getImgUrls(el), video: this.getVideoUrls(el)}, 
                metadata: {id: this.getID(el)}};
    }
};