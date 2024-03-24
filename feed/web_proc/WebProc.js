class InvalidPostError extends Error {};
class WebProcUndefinedError extends Error {};

class WebProc {
    getPostFromChildEl(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
    getRelevantData(el) {
        throw new WebProcUndefinedError("Processing undefined for this website");
    }
};