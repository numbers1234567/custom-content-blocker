const FILTER_API_URL = "http://127.0.0.1:8000";//"[API URL here]";
var current_key = "admin";

function filter_post(post_data) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${FILTER_API_URL}/process_post/${current_key}/`);
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    const body = JSON.stringify(post_data);
    console.log(body);
    xhr.onload = () => {
        console.log("Success");
    }
    xhr.send(body);
    console.log(`${FILTER_API_URL}/process_post/${current_key}/`);
}