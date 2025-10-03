/**
 * Load the full job log once, then subscribe to SSE for incremental updates.
 * Keeps auto-scroll behaviour and handles errors gracefully.
 */
(function () {
  const jobLogDiv = document.getElementById("job-log");
  if (!jobLogDiv) {
    // Nothing to do if the element is missing.
    return;
  }

  const streamUrl = jobLogDiv.getAttribute("data-stream-url");
  const fullLogUrl = jobLogDiv.getAttribute("data-full-log-url");

  /**
   * Append a single log line to the job log container.
   * @param {string} line
   */
  function appendLine(line) {
    const p = document.createElement("p");
    p.textContent = line;
    jobLogDiv.appendChild(p);
  }

  /**
   * Load the full log via fetch and render it.
   */
  async function loadFullLog() {
    if (!fullLogUrl) {
      return;
    }
    try {
      const resp = await fetch(fullLogUrl, { credentials: "same-origin" });
      if (!resp.ok) {
        appendLine(`Error fetching full log: ${resp.status}`);
        return;
      }
      const text = await resp.text();
      if (text) {
        // Render each line as a paragraph.
        text.split(/\r?\n/).forEach((line) => {
          if (line.length > 0) {
            appendLine(line);
          }
        });
        // Scroll to bottom after initial load.
        jobLogDiv.scrollTop = jobLogDiv.scrollHeight;
      }
    } catch (err) {
      appendLine(`Error loading log: ${err}`);
    }
  }

  /**
   * Start EventSource to receive appended log lines.
   */
  function startSSE() {
    if (!streamUrl) {
      return;
    }
    const es = new EventSource(streamUrl);
    es.onmessage = function (event) {
      // Server sends raw lines in event.data; append and scroll.
      appendLine(event.data);
      jobLogDiv.scrollTop = jobLogDiv.scrollHeight;
    };
    es.addEventListener("error", function (event) {
      // If server emits an error event, show it and close the connection.
      const errText = event.data || "SSE error";
      const p = document.createElement("p");
      p.style.color = "red";
      p.textContent = errText;
      jobLogDiv.appendChild(p);
      es.close();
    });
    es.onerror = function () {
      console.error("Error occurred in SSE connection.");
      es.close();
    };
  }

  // Initialize: load existing content, then stream updates.
  loadFullLog().then(startSSE);
})();
