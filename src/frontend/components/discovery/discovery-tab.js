"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import TickerSelect from "./ticker-select.js";
import controls from "../shared/controls.module.css";
import styles from "./discovery-tab.module.css";

export default function DiscoveryTab({
  active,
  marketTickers,
  marketProgress,
  marketLoading,
  marketError,
  collectionMode,
  stopping,
  deletingTicker,
  messages,
  onCollect,
  onStop
}) {
  const [tickerToAdd, setTickerToAdd] = useState("");
  const messagesRef = useRef(null);
  const followMessagesRef = useRef(true);
  const seenPercentage = marketProgress?.total
    ? (100 * marketProgress.seen / marketProgress.total).toFixed(1)
    : "0.0";

  useEffect(() => {
    setTickerToAdd((current) => marketTickers.includes(current) ? current : "");
  }, [marketTickers]);

  useLayoutEffect(() => {
    const textbox = messagesRef.current;
    if (active && followMessagesRef.current) {
      textbox.scrollTop = textbox.scrollHeight;
    }
  }, [messages, active]);

  function collectStocks(ticker) {
    followMessagesRef.current = true;
    onCollect(ticker);
  }

  return (
    <div role="tabpanel" id="panel-discover" aria-labelledby="tab-discover" hidden={!active}>
      <div className={styles.discoveryControls}>
        <button
          type="button"
          className={`${controls.button} ${controls.primary}`}
          onClick={() => collectStocks()}
          disabled={Boolean(collectionMode || deletingTicker)}
          aria-busy={collectionMode === "discover"}
        >
          {collectionMode === "discover" ? "Loading…" : "Discover"}
        </button>
        {collectionMode === "discover" && (
          <button
            type="button"
            className={`${controls.button} ${controls.primary}`}
            onClick={onStop}
            disabled={stopping}
            aria-busy={stopping}
          >
            {stopping ? "Stopping…" : "Stop"}
          </button>
        )}
      </div>
      <form
        className={styles.addStockControls}
        onSubmit={(event) => {
          event.preventDefault();
          if (tickerToAdd) collectStocks(tickerToAdd);
        }}
      >
        <TickerSelect
          tickers={marketTickers}
          value={tickerToAdd}
          onChange={setTickerToAdd}
          disabled={Boolean(collectionMode || deletingTicker) || marketLoading || marketTickers.length === 0}
        />
        <button
          type="submit"
          className={`${controls.button} ${controls.primary}`}
          disabled={Boolean(collectionMode || deletingTicker) || marketLoading || !marketTickers.includes(tickerToAdd)}
          aria-busy={collectionMode === "add"}
        >
          {collectionMode === "add" ? "Adding…" : "Add"}
        </button>
      </form>
      {marketError && <p role="alert">Failed to load market tickers: {marketError}</p>}
      {!marketLoading && !marketError && marketTickers.length === 0 && (
        <p>No new tickers available to add.</p>
      )}
      <div
        ref={messagesRef}
        className={styles.discoveryMessages}
        role="log"
        aria-label="Stock collection status messages"
        aria-live="polite"
        aria-relevant="additions text"
        tabIndex={0}
        onScroll={({ currentTarget }) => {
          if (currentTarget.clientHeight === 0) return;
          followMessagesRef.current = currentTarget.scrollHeight
            - currentTarget.clientHeight - currentTarget.scrollTop <= 1;
        }}
      >
        {messages.map(({ timestamp, messageType, message, separator }, index) => (
          separator ? <br key={index} aria-hidden="true" /> :
          <div key={index}>
            <time dateTime={timestamp.replace(" ", "T")}>{timestamp}</time>
            {" ["}<span className={styles[messageType]}>{messageType}</span>{"]\t"}
            {message}
          </div>
        ))}
      </div>
      {marketProgress && (
        <p className={styles.marketProgress} role="status">
          {marketProgress.seen}/{marketProgress.total} ({seenPercentage}%) of stocks seen
        </p>
      )}
    </div>
  );
}
