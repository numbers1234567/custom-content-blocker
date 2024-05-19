class InvalidPostError extends Error {};
class WebProcUndefinedError extends Error {};

class WebProc {
    // The following gets data from a specific post.
    getPostFromChildEl(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getImgData(el) { // Return as a list of promises as {content : string, dataFormat : string}
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getVidData(el) { // Return as a list of promises as {content : string, dataFormat : string}
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getText(el) { // Return as a string
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getID(el) { // Return as a string
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getRelevantData(el) { // Get some data from a post. Return Promise of data since images and video are huge.
        // Shouldn't need to overload this.
        el = this.getPostFromChildEl(el);
        let procObj = this;
        return new Promise(function(resolve, reject) { // ew
            Promise.all(procObj.getImgData(el)).then(
            (imgData) => {
                Promise.all(procObj.getVidData(el)).then(
                (vidData) => {
                    let res = {media: {text: procObj.getText(el), images: imgData, video: vidData}, 
                    metadata: {id: procObj.getID(el)}};
                    resolve(res);
                })
            })
        });
    }
    // Data node where posts are dynamically loaded
    getDataNode(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getDomUpdateData(mutationList) { // {"data" : getRelevantData, "post" : node} from dom updates, so getting data from newly loaded posts
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
};