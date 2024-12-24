const jobLogDiv = document.getElementById("job-log");
const streamUrl = jobLogDiv.getAttribute("data-stream-url");
const eventSource = new EventSource(streamUrl);

eventSource.onmessage = function(event) {
    const newLogEntry = document.createElement("p");
    newLogEntry.textContent = event.data;
    jobLogDiv.appendChild(newLogEntry);
    jobLogDiv.scrollTop = jobLogDiv.scrollHeight; // Auto-scroll to the bottom
};

eventSource.addEventListener('error', function(event) {
    const errorMessage = document.createElement("p");
    errorMessage.style.color = "red";
    errorMessage.textContent = event.data;
    jobLogDiv.appendChild(errorMessage);
    eventSource.close(); // Stop listening after error
});

eventSource.onerror = function() {
    console.error("Error occurred in SSE connection.");
    eventSource.close();
};
