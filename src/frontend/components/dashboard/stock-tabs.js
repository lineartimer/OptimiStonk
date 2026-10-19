"use client";

import styles from "./stock-tabs.module.css";

const tabs = [
  { id: "discover", label: "Add stock(s)" },
  { id: "stock-details", label: "Stock details" },
  { id: "search", label: "Search" }
];

export default function StockTabs({ value, onChange }) {
  return (
    <div className={styles.tabs} role="tablist" aria-label="Stock controls">
      {tabs.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          role="tab"
          id={`tab-${id}`}
          aria-selected={value === id}
          aria-controls={`panel-${id}`}
          onClick={() => onChange(id)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
