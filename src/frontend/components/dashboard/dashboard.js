"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { request } from "../../lib/api.js";
import { numericValue } from "../../lib/format.js";
import StockSidebar from "../stock-sidebar/stock-sidebar.js";
import DiscoveryTab from "../discovery/discovery-tab.js";
import { log } from "../discovery/logger.js";
import StockDetailsTab from "../stock-details/stock-details-tab.js";
import DeleteStockDialog from "../stock-details/delete-stock-dialog.js";
import SearchTab from "../search/search-tab.js";
import StockTabs from "./stock-tabs.js";
import styles from "./dashboard.module.css";

function compareTickers(a, b) {
  return a.ticker.localeCompare(b.ticker, "en", { sensitivity: "base" });
}

export default function Dashboard() {
  const [companies, setCompanies] = useState([]);
  const [companiesLoading, setCompaniesLoading] = useState(true);
  const [companiesError, setCompaniesError] = useState("");
  const [selectedTicker, setSelectedTicker] = useState(null);
  const [tickerToDelete, setTickerToDelete] = useState(null);
  const [deletingTicker, setDeletingTicker] = useState(null);
  const [deleteError, setDeleteError] = useState(null);
  const deleteButtonRef = useRef(null);
  const [marketTickers, setMarketTickers] = useState([]);
  const [marketLoading, setMarketLoading] = useState(true);
  const [marketError, setMarketError] = useState("");
  const [sort, setSort] = useState({ key: "rank", direction: "descending" });
  const [tab, setTab] = useState("stock-details");
  const [collectionMode, setCollectionMode] = useState(null);
  const [stopping, setStopping] = useState(false);
  const collectionRunRef = useRef(null);
  const [discoveryMessages, setDiscoveryMessages] = useState([]);

  function addDiscoveryMessage(message, messageType = "info", newLine = true) {
    const receivedAt = new Date();
    setDiscoveryMessages((messages) => (
      log(messages, message, messageType, newLine, receivedAt)
    ));
  }

  const sortedCompanies = useMemo(() => {
    const direction = sort.direction === "ascending" ? 1 : -1;

    return [...companies].sort((a, b) => {
      if (sort.key === "ticker") return direction * compareTickers(a, b);

      const aValue = numericValue(a[sort.key]);
      const bValue = numericValue(b[sort.key]);

      if (aValue == null && bValue == null) return compareTickers(a, b);

      if (aValue == null) return 1;

      if (bValue == null) return -1;

      return direction * (aValue - bValue) || compareTickers(a, b);
    });
  }, [companies, sort]);

  const company = companies.find(({ ticker }) => ticker === selectedTicker)
    || sortedCompanies[0];

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
    if (collectionRunRef.current) collectionRunRef.current.stopRequested = true;
  }, []);

  const loadMarket = useCallback(async (signal) => {
    setMarketLoading(true);
    setMarketError("");

    try {
      const tickers = await request("/api/market", signal);
      if (signal?.aborted) return;

      setMarketTickers(tickers);
    } catch (error) {
      if (!signal?.aborted) {
        setMarketError(error.message);
        setMarketTickers([]);
      }
    } finally {
      if (!signal?.aborted) setMarketLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    loadMarket(controller.signal);
    return () => controller.abort();
  }, [loadMarket]);

  async function collectStocks(ticker) {
    if (collectionRunRef.current || deletingTicker) return;
    if (ticker && (marketLoading || !marketTickers.includes(ticker))) return;

    const run = { stopRequested: false };
    collectionRunRef.current = run;
    setCollectionMode(ticker ? "add" : "discover");
    setStopping(false);

    try {
      while (!run.stopRequested) {
        try {
          const path = ticker
            ? `/api/stock?ticker=${encodeURIComponent(ticker)}`
            : "/api/discover";
          await request(path, undefined, addDiscoveryMessage);
          await loadCompanies();
        } catch (error) {
          addDiscoveryMessage(error.message, "error");
          if (ticker || !error.stockFailure) break;
        } finally {
          await loadMarket();
        }

        setDiscoveryMessages((messages) => [...messages, { separator: true }]);
        if (ticker) break;
      }
    } finally {
      collectionRunRef.current = null;

      setCollectionMode(null);
      setStopping(false);
    }
  }

  function stopDiscovery() {
    const run = collectionRunRef.current;
    if (!run || run.stopRequested) return;

    run.stopRequested = true;
    setStopping(true);
  }

  async function deleteCompany() {
    if (tickerToDelete === null || deletingTicker || collectionMode || companiesLoading) return;

    const ticker = tickerToDelete;
    setTickerToDelete(null);
    setDeletingTicker(ticker);
    setDeleteError(null);

    try {
      await request(`/api/stock?ticker=${encodeURIComponent(ticker)}`, undefined, undefined, "DELETE");
      setCompanies((current) => current.filter((item) => item.ticker !== ticker));
      setSelectedTicker((current) => current === ticker ? null : current);
      await loadMarket();
    } catch (error) {
      setDeleteError({ ticker, message: `Failed to delete ${ticker}: ${error.message}` });
    } finally {
      setDeletingTicker(null);
    }
  }

  return (
    <main className={styles.page}>
      <StockSidebar
        companies={sortedCompanies}
        selectedTicker={company?.ticker}
        companiesLoading={companiesLoading}
        companiesError={companiesError}
        sort={sort}
        onSort={sortBy}
        onSelect={(ticker) => {
          setSelectedTicker(ticker);
          setTab("stock-details");
        }}
        inert={tickerToDelete !== null}
      />
      <section className={styles.content} inert={tickerToDelete !== null}>
        <StockTabs value={tab} onChange={setTab} />
        {/* Keep panels mounted so tab changes preserve input and request state. */}
        <DiscoveryTab
          active={tab === "discover"}
          marketTickers={marketTickers}
          marketLoading={marketLoading}
          marketError={marketError}
          collectionMode={collectionMode}
          stopping={stopping}
          deletingTicker={deletingTicker}
          messages={discoveryMessages}
          onCollect={collectStocks}
          onStop={stopDiscovery}
        />
        <StockDetailsTab
          active={tab === "stock-details"}
          company={company}
          companiesLoading={companiesLoading}
          deletingTicker={deletingTicker}
          collectionMode={collectionMode}
          deleteError={deleteError}
          deleteButtonRef={deleteButtonRef}
          onDelete={setTickerToDelete}
        />
        <SearchTab active={tab === "search"} />
      </section>
      {tickerToDelete !== null && (
        <DeleteStockDialog
          ticker={tickerToDelete}
          returnFocusRef={deleteButtonRef}
          onCancel={() => setTickerToDelete(null)}
          onConfirm={deleteCompany}
        />
      )}
    </main>
  );
}
