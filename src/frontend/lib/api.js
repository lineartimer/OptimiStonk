export async function request(path, signal, onStatus, method = "GET") {
  const response = await fetch(path, { cache: "no-store", signal, method });
  if (response.status === 204) return;

  if (response.ok && response.headers.get("content-type")?.includes("application/x-ndjson")) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });

        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;

          const event = JSON.parse(line);

          if (event.type === "status") {
            onStatus?.(event.message, event.message_type, event.new_line);
          }

          if (event.type === "result") return event.data;

          if (event.type === "error") {
            const error = new Error(event.detail);

            // Stock failures have already been recorded and can be skipped.
            // A bare 404 means the market is exhausted, not a missing ticker.
            error.stockFailure = event.status_code === 422
              || (event.status_code === 404 && event.detail !== "Not Found")
              || (event.status_code === 500 && (
                event.detail === "Failed to load stock data."
                || event.detail.startsWith("Failed to load stock data: ")
              ));

            throw error;
          }
        }

        if (done) throw new Error("Stock collection stream ended before a result was received.");
      }
    } finally {
      await reader.cancel();
      reader.releaseLock();
    }
  }

  const body = await response.text();
  let data;

  try {
    data = JSON.parse(body);
  } catch {
    if (response.ok) throw new Error("Failed to interpret response from backend.");
  }

  if (!response.ok) {
    throw new Error(data?.detail || body || response.statusText);
  }

  return data;
}
