"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import styles from "./page.module.css";

async function request(path, signal) {
  const response = await fetch(path, { cache: "no-store", signal });
  const body = await response.text();
  let data;

  try {
    data = JSON.parse(body);
  } catch {
    if (response.ok) throw new Error("Invalid response from the server.");
  }

  if (!response.ok) {
    throw new Error(data?.detail || body || response.statusText);
  }

  return data;
}

function CompanySummary({ text }) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const summaryRef = useRef(null);
  const summaryId = useId();

  useEffect(() => {
    if (expanded) return;

    const summary = summaryRef.current;
    const updateOverflow = () => {
      setCanExpand(summary.scrollHeight > summary.clientHeight);
    };
    const observer = new ResizeObserver(updateOverflow);

    updateOverflow();
    observer.observe(summary);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <>
      <p
        id={summaryId}
        ref={summaryRef}
        className={`${styles.summary} ${expanded ? "" : styles.summaryCollapsed}`}
      >
        {text}
      </p>
      {canExpand && (
        <button
          type="button"
          className={styles.summaryToggle}
          aria-expanded={expanded}
          aria-controls={summaryId}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </>
  );
}

export default function Home() {
  const [companies, setCompanies] = useState([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);
  const [companiesError, setCompaniesError] = useState("");
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [tab, setTab] = useState("Company");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const company = companies.find(({ ticker }) => ticker === selectedTicker)
    || companies[0];

  const loadCompanies = useCallback(async (signal) => {
    setCompaniesLoading(true);
    setCompaniesError("");

    try {
      setCompanies(await request("/api/companies", signal));
    } catch (error) {
      if (!signal?.aborted) setCompaniesError(error.message);
    } finally {
      if (!signal?.aborted) setCompaniesLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadCompanies(controller.signal);
    return () => controller.abort();
  }, [loadCompanies]);

  async function search() {
    if (loading) return;

    setLoading(true);
    setStatus("");

    try {
      await request("/api/search");
      setStatus("Company added successfully.");
      await loadCompanies();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <aside className={styles.sidebar} aria-label="Companies">
        <h2>Companies</h2>
        {companiesLoading && <p role="status">Loading companies…</p>}
        {companiesError && <p role="alert">{companiesError}</p>}
        {!companiesLoading && !companiesError && companies.length === 0 && (
          <p>No companies yet. Use Search to add one.</p>
        )}
        <ul className={styles.companies}>
          {companies.map((item) => (
            <li key={item.ticker}>
              <button
                type="button"
                aria-current={company?.ticker === item.ticker ? "true" : undefined}
                onClick={() => {
                  setSelectedTicker(item.ticker);
                  setTab("Company");
                }}
              >
                {item.name}
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <section className={styles.content}>
        <div className={styles.tabs} role="tablist" aria-label="Company tools">
          {["Search", "Company"].map((name) => (
            <button
              key={name}
              type="button"
              role="tab"
              id={`tab-${name}`}
              aria-selected={tab === name}
              aria-controls={`panel-${name}`}
              onClick={() => setTab(name)}
            >
              {name}
            </button>
          ))}
        </div>

        <div role="tabpanel" id="panel-Search" aria-labelledby="tab-Search" hidden={tab !== "Search"}>
          <button type="button" onClick={search} disabled={loading}>
            {loading ? "Loading…" : "Search"}
          </button>
          <p role="status">{status}</p>
        </div>

        <div role="tabpanel" id="panel-Company" aria-labelledby="tab-Company" hidden={tab !== "Company"}>
          {company ? (
            <>
              <h1>{company.name}</h1>
              <p>Ticker: {company.ticker}</p>
              <CompanySummary
                key={company.ticker}
                text={company.summary || "No summary available."}
              />
            </>
          ) : (
            <p>{companiesLoading ? "Loading company details…" : "No company selected."}</p>
          )}
        </div>
      </section>
    </main>
  );
}
