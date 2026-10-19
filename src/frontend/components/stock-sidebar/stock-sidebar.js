"use client";

import { formatRank } from "../../lib/format.js";
import styles from "./stock-sidebar.module.css";

const stockColumns = [
  { key: "ticker", label: "Ticker" },
  { key: "rank", label: "Rank" }
];

export default function StockSidebar({
  companies,
  selectedTicker,
  companiesLoading,
  companiesError,
  sort,
  onSort,
  onSelect,
  inert
}) {
  return (
    <aside className={styles.sidebar} aria-label="Stocks" inert={inert}>
      <a href="/" aria-label="OptimiStonk home">
        <span className={styles.logo} aria-hidden="true" />
      </a>
      {companiesLoading && <p role="status">Loading companies…</p>}
      {companiesError && <p role="alert">{companiesError}</p>}
      <div className={styles.companiesScroll}>
        <table className={styles.companies} aria-label="Stocks">
          <thead>
            <tr>
              {stockColumns.map(({ key, label }) => (
                <th
                  key={key}
                  scope="col"
                  aria-sort={sort.key === key ? sort.direction : "none"}
                >
                  <button type="button" aria-label={label} onClick={() => onSort(key)}>
                    {label.split(" ").join("\n")}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {companies.map((item) => (
              <tr
                key={item.ticker}
                className={selectedTicker === item.ticker ? styles.selectedCompany : undefined}
                onClick={() => onSelect(item.ticker)}
              >
                <td>
                  <button
                    type="button"
                    title={item.name}
                    aria-current={selectedTicker === item.ticker ? "true" : undefined}
                  >
                    {item.ticker}
                  </button>
                </td>
                <td>{formatRank(item.rank)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </aside>
  );
}
