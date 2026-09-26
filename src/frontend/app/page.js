"use client";

import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import { log } from "./logger.mjs";
import styles from "./page.module.css";

const stockColumns = [
  { key: "ticker", label: "Ticker" },
  { key: "rank_backlog", label: "Rank Backlog" },
  { key: "rank_market", label: "Rank Market" }
];

const tabs = [
  { id: "discover", label: "Discover" },
  { id: "stock-details", label: "Stock details" }
];

function compareTickers(a, b) {
  return a.ticker.localeCompare(b.ticker, "en", { sensitivity: "base" });
}

async function request(path, signal, onStatus) {
  const response = await fetch(path, { cache: "no-store", signal });
  if (response.ok && onStatus) {
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

          if (event.type === "status") onStatus(event.message, event.message_type, event.new_line);
          if (event.type === "result") return event.data;
          if (event.type === "error") {
            const error = new Error(event.detail);

            // Stock failures have already been recorded and can be skipped.
            // A bare 404 means the market is exhausted, not a missing ticker.
            error.stockFailure = event.status_code === 422
              || (event.status_code === 404 && event.detail !== "Not Found")
              || (event.status_code === 500 && event.detail === "Failed to load stock data.");
            
              throw error;
          }
        }

        if (done) throw new Error("Discovery stream ended before a result was received.");
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
  const [sort, setSort] = useState({ key: "ticker", direction: "ascending" });
  const [tab, setTab] = useState("stock-details");
  const [loading, setLoading] = useState(false);
  const [stopping, setStopping] = useState(false);
  const discoveryRunRef = useRef(null);
  const [discoveryMessages, setDiscoveryMessages] = useState([]);
  const discoveryMessagesRef = useRef(null);
  const followMessagesRef = useRef(true);

  useLayoutEffect(() => {
    const textbox = discoveryMessagesRef.current;
    if (tab === "discover" && followMessagesRef.current) {
      textbox.scrollTop = textbox.scrollHeight;
    }
  }, [discoveryMessages, tab]);

  function addDiscoveryMessage(message, messageType = "info", newLine = true) {
    const receivedAt = new Date();
    setDiscoveryMessages((messages) => (
      log(messages, message, messageType, newLine, receivedAt)
    ));
  }

  const company = companies.find(({ ticker }) => ticker === selectedTicker)
    || companies[0];

  const sortedCompanies = useMemo(() => {
    const direction = sort.direction === "ascending" ? 1 : -1;

    return [...companies].sort((a, b) => {
      if (sort.key === "ticker") return direction * compareTickers(a, b);

      const aValue = a[sort.key];
      const bValue = b[sort.key];

      if (aValue == null && bValue == null) return compareTickers(a, b);
      
      if (aValue == null) return 1;
      
      if (bValue == null) return -1;

      return direction * (aValue - bValue) || compareTickers(a, b);
    });
  }, [companies, sort]);

  function sortBy(key) {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "ascending"
        ? "descending"
        : "ascending"
    }));
  }

  const loadCompanies = useCallback(async (signal) => {
    setCompaniesLoading(true);
    setCompaniesError("");

    try {
      const data = await request("/api/stock", signal);
      setCompanies((Array.isArray(data) ? data : [data]).sort(compareTickers));
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

  useEffect(() => () => {
    if (discoveryRunRef.current) discoveryRunRef.current.stopRequested = true;
  }, []);

  async function search() {
    if (discoveryRunRef.current) return;

    const run = { stopRequested: false };
    discoveryRunRef.current = run;
    setLoading(true);
    setStopping(false);
    followMessagesRef.current = true;

    try {
      while (!run.stopRequested) {
        try {
          await request("/api/discover", undefined, addDiscoveryMessage);
          await loadCompanies();
        } catch (error) {
          addDiscoveryMessage(error.message, "error");
          if (!error.stockFailure) break;
        }
        
        setDiscoveryMessages((messages) => [...messages, { separator: true }]);
      }
    } finally {
      discoveryRunRef.current = null;

      setLoading(false);
      setStopping(false);
    }
  }

  function stopDiscovery() {
    const run = discoveryRunRef.current;
    if (!run || run.stopRequested) return;

    run.stopRequested = true;
    setStopping(true);
  }

  return (
    <main className={styles.page}>
      <aside className={styles.sidebar} aria-label="Stocks">
        <a href="/" aria-label="OptimiStonk home">
          <Image
            className={styles.logo}
            src="/images/logo.png"
            alt="OptimiStonk"
            width={216}
            height={72}
            loading="eager"
          />
        </a>
        {companiesLoading && <p role="status">Loading companies…</p>}
        {companiesError && <p role="alert">{companiesError}</p>}
        {!companiesLoading && !companiesError && companies.length === 0 && (
          <p>Use Discover to add companies.</p>
        )}
        <table className={styles.companies} aria-label="Stocks">
          <thead>
            <tr>
              {stockColumns.map(({ key, label }) => (
                <th
                  key={key}
                  scope="col"
                  aria-sort={sort.key === key ? sort.direction : "none"}
                >
                  <button type="button" aria-label={label} onClick={() => sortBy(key)}>
                    {label.split(" ").join("\n")}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedCompanies.map((item) => (
              <tr
                key={item.ticker}
                className={company?.ticker === item.ticker ? styles.selectedCompany : undefined}
                onClick={() => setSelectedTicker(item.ticker)}
              >
                <td>
                  <button
                    type="button"
                    title={item.name}
                    aria-current={company?.ticker === item.ticker ? "true" : undefined}
                  >
                    {item.ticker}
                  </button>
                </td>
                <td>{item.rank_backlog ?? "—"}</td>
                <td>{item.rank_market ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </aside>

      <section className={styles.content}>
        <div className={styles.tabs} role="tablist" aria-label="Stock controls">
          {tabs.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              id={`tab-${id}`}
              aria-selected={tab === id}
              aria-controls={`panel-${id}`}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        <div role="tabpanel" id="panel-discover" aria-labelledby="tab-discover" hidden={tab !== "discover"}>
          <div className={styles.discoveryControls}>
            <button type="button" onClick={search} disabled={loading}>
              {loading ? "Loading…" : "Discover"}
            </button>
            {loading && (
              <button type="button" onClick={stopDiscovery} disabled={stopping}>
                {stopping ? "Stopping…" : "Stop"}
              </button>
            )}
          </div>
          <div
            ref={discoveryMessagesRef}
            className={styles.discoveryMessages}
            role="log"
            aria-label="Discovery status messages"
            aria-live="polite"
            aria-relevant="additions text"
            tabIndex={0}
            onScroll={({ currentTarget }) => {
              if (currentTarget.clientHeight === 0) return;
              followMessagesRef.current = currentTarget.scrollHeight
                - currentTarget.clientHeight - currentTarget.scrollTop <= 1;
            }}
          >
            {discoveryMessages.map(({ timestamp, messageType, message, separator }, index) => (
              separator ? <br key={index} aria-hidden="true" /> :
              <div key={index}>
                <time dateTime={timestamp.replace(" ", "T")}>{timestamp}</time>
                {" ["}<span className={styles[messageType]}>{messageType}</span>{"]\t"}
                {message}
              </div>
            ))}
          </div>
        </div>

        <div role="tabpanel" id="panel-stock-details" aria-labelledby="tab-stock-details" hidden={tab !== "stock-details"}>
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
