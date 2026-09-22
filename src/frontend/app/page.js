"use client";

import { useState } from "react";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState("");

  async function scout() {
    if (loading) return;

    setLoading(true);
    setOutput("");

    try {
      const response = await fetch("/api/scout", { cache: "no-store" });
      const body = await response.text();
      let formatted = body;

      try {
        formatted = JSON.stringify(JSON.parse(body), null, 2);
      } catch {
        // Keep plain-text responses, such as proxy errors, readable.
      }

      setOutput(
        response.ok
          ? formatted
          : `Error ${response.status}: ${formatted || response.statusText}`,
      );
    } catch (error) {
      setOutput(`Request failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <button type="button" onClick={scout} disabled={loading}>
        {loading ? "Loading…" : "Scout"}
      </button>
      <pre aria-live="polite">{output}</pre>
    </main>
  );
}
