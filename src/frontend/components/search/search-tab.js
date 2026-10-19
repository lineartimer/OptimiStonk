"use client";

import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { request } from "../../lib/api.js";
import ReferencePreview from "./reference-preview.js";
import controls from "../shared/controls.module.css";
import markdown from "./markdown.module.css";
import styles from "./search-tab.module.css";

export default function SearchTab({ active }) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResult, setSearchResult] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");

  async function search(event) {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query || searchLoading) return;

    setSearchLoading(true);
    setSearchError("");
    setSearchResult(null);

    try {
      setSearchResult(await request(`/api/rag?query=${encodeURIComponent(query)}`));
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setSearchLoading(false);
    }
  }

  return (
    <div role="tabpanel" id="panel-search" aria-labelledby="tab-search" hidden={!active}>
      <form className={styles.searchControls} onSubmit={search}>
        <input
          type="text"
          aria-label="Search query"
          placeholder="Ask a question about companies"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          disabled={searchLoading}
        />
        <button
          type="submit"
          className={`${controls.button} ${controls.primary}`}
          disabled={searchLoading || !searchQuery.trim()}
          aria-busy={searchLoading}
        >
          {searchLoading ? "Searching…" : "Search"}
        </button>
      </form>
      {searchLoading && <p role="status">Searching filings…</p>}
      {searchError && <p className={controls.error} role="alert">{searchError}</p>}
      {searchResult && (
        <div aria-live="polite">
          <div className={markdown.markdown}>
            <Markdown remarkPlugins={[remarkGfm]}>{searchResult.result}</Markdown>
          </div>
          <h2>References</h2>
          {searchResult.sources.length > 0 ? (
            <ol>
              {searchResult.sources.map(({ title, source }, index) => (
                <li key={index}>
                  <ReferencePreview title={title} text={source} />
                </li>
              ))}
            </ol>
          ) : <p>No references available.</p>}
        </div>
      )}
    </div>
  );
}
