class InvalidPostError extends Error {};
class WebProcUndefinedError extends Error {};

class WebProc {
    // The following gets data from a specific post.
    getPostFromChildEl(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getImgData(el) { // Return as a list of {content : [Promise of Raw Data as a string], dataFormat : string}
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getVidData(el) { // Return as a list of {content : [Promise of Raw Data as a string], dataFormat : string}
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getText(el) { // Return as a string
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getID(el) { // Return as a string
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getRelevantData(el) { // Get some data from a post. Shouldn't need to overload this.
        el = this.getPostFromChildEl(el);
        return {media: {text: this.getText(el), images: this.getImgData(el), video: this.getVidData(el)}, 
        metadata: {id: this.getID(el)}};
    }
    // Data node where posts are dynamically loaded
    getDataNode(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getDomUpdateData(mutationList) { // getRelevantData from dom updates, so getting data from newly loaded posts
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
};