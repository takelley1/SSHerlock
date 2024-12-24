/**
 * Initializes the EventSource to stream job logs.
 * The job log is displayed in the jobLogDiv element.
 */
const jobLogDiv = document.getElementById("job-log");
const streamUrl = jobLogDiv.getAttribute("data-stream-url");
const eventSource = new EventSource(streamUrl);

/**
 * Handles incoming messages from the EventSource.
 * Appends new log entries to the job log div.
 */
eventSource.onmessage = function(event) {
    const newLogEntry = document.createElement("p");
    newLogEntry.textContent = event.data;
    jobLogDiv.appendChild(newLogEntry);
    jobLogDiv.scrollTop = jobLogDiv.scrollHeight; // Auto-scroll to the bottom of the log
};

/**
 * Handles errors from the EventSource.
 * Displays an error message in the job log div and closes the connection.
 */
eventSource.addEventListener('error', function(event) {
    const errorMessage = document.createElement("p");
    errorMessage.style.color = "red";
    errorMessage.textContent = event.data;
    jobLogDiv.appendChild(errorMessage);
    eventSource.close(); // Stop listening after an error occurs
});

/**
 * Handles generic errors in the EventSource connection.
 * Logs the error to the console and closes the connection.
 */
eventSource.onerror = function() {
    console.error("Error occurred in SSE connection.");
    eventSource.close();
};
