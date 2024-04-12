const FILTER_API_URL = "http://127.0.0.1:8000";//"[API URL here]";
var current_key = "admin";

function filter_post(post_data) {
    
    // Send the POST request using fetch
    fetch(`${FILTER_API_URL}/process_post/${current_key}/`, {
        method: "POST",
        mode: "no-cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(post_data)
    }).then(
        (data) => {
            console.log(data);
        }
    ).catch(
        (error) => {
            console.log(error);
        }
    );
    //.then((response) => response.json())
    //.then((data) => console.log("Success:", data));
}