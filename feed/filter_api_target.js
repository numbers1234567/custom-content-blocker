const FILTER_API_URL = "http://localhost:8000";//"[API URL here]";
var current_key = "admin";

// Add post to backend database. Determine if block
function processPost(post_data, block_callback) {
    // Send the POST request using fetch
    fetch(`${FILTER_API_URL}/process_post/${current_key}/`, {
        method: "POST",
        mode: "cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(post_data)
    }
    ).then((response) => response.json()
    ).then((data) => {
        if (data["block_score"] > 0.5) block_callback();
    });
}

// Post is assumed to be stored in backend database
function processBlock(post_id) {

}