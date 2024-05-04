function getRawPixelData(el) {
    return new Promise(function(resolve, reject) {
        // To avoid SecurityError
        el.setAttribute("crossorigin", "anonymous");
        let loadData = function() {
            // File format
            let format = "png";
            
            // Draw image to canvas and get canvas content
            var canvas = document.createElement("canvas");

            canvas.width = el.width;
            canvas.height = el.height;

            if (el.width==0 || el.height==0) reject("Could not load image.");

            var ctx = canvas.getContext("2d");
            ctx.drawImage(el, 0, 0);

            var dataURL = canvas.toDataURL("image/" + format);
            resolve({content : dataURL.split(",")[1], dataFormat : format});
        }
        if (el.complete) loadData();
        else el.onload = loadData
    }); 
}