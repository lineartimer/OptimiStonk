"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import styles from "./page.module.css";

const companyColumns = [
  { key: "ticker", label: "Ticker" },
  { key: "rank_backlog", label: "Rank Backlog" },
  { key: "rank_market", label: "Rank Market" },
];

function compareTickers(a, b) {
  return a.ticker.localeCompare(b.ticker, "en", { sensitivity: "base" });
}

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
  const [sort, setSort] = useState({ key: "ticker", direction: "ascending" });
  const [tab, setTab] = useState("Company");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

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
        : "ascending",
    }));
  }

  const loadCompanies = useCallback(async (signal) => {
    setCompaniesLoading(true);
    setCompaniesError("");

    try {
      const data = await request("/api/company", signal);
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
        <table className={styles.companies} aria-label="Companies">
          <thead>
            <tr>
              {companyColumns.map(({ key, label }) => (
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
              >
                <td>
                  <button
                    type="button"
                    title={item.name}
                    aria-current={company?.ticker === item.ticker ? "true" : undefined}
                    onClick={() => {
                      setSelectedTicker(item.ticker);
                      setTab("Company");
                    }}
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
