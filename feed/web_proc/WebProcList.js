// Define web processing
if (new RegExp(".*://.*\.reddit\..*/.*").test(document.URL)) proc = new RedditProc();
else proc = new WebProc();