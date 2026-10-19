"use client";

import { Fragment } from "react";
import { formatMillions, formatPrice, formatRatio } from "../../lib/format.js";
import CompanySummary from "./company-summary.js";
import StockHistoryChart from "./stock-history-chart.js";
import controls from "../shared/controls.module.css";
import styles from "./stock-details-tab.module.css";

const ratioFields = [
  { key: "price_to_earnings_ratio", label: "P/E" },
  { key: "revenue_growth_per_year", label: "Annual revenue growth", percentage: true },
  { key: "quick_ratio", label: "Quick ratio" },
  { key: "leverage", label: "Leverage" },
  { key: "asset_turnover", label: "Asset turnover" },
  { key: "operating_margin", label: "Operating margin", percentage: true },
  { key: "r_and_d_to_revenue", label: "R&D-to-revenue", percentage: true }
];

export default function StockDetailsTab({
  active,
  company,
  companiesLoading,
  deletingTicker,
  collectionMode,
  deleteError,
  deleteButtonRef,
  onDelete
}) {
  return (
    <div role="tabpanel" id="panel-stock-details" aria-labelledby="tab-stock-details" hidden={!active}>
      {company ? (
        <>
          <div className={styles.companyHeading}>
            <h1>{company.name}</h1>
            <button
              ref={deleteButtonRef}
              type="button"
              className={`${controls.button} ${controls.danger}`}
              disabled={Boolean(deletingTicker || collectionMode || companiesLoading)}
              aria-busy={deletingTicker === company.ticker}
              onClick={() => onDelete(company.ticker)}
            >
              {deletingTicker === company.ticker ? "Deleting…" : "Delete"}
            </button>
          </div>
          {deleteError?.ticker === company.ticker && (
            <p className={controls.error} role="alert">{deleteError.message}</p>
          )}
          <p>
            <span className={styles.stockIdentity}>
              {company.ticker}{company.stock_exchange ? `:${company.stock_exchange}` : ""}
            </span>{" "}
            <strong title="Latest collected price">{formatPrice(company.last_price)}</strong>
          </p>
          <CompanySummary
            key={company.ticker}
            text={company.summary || "No summary available."}
          />
          {active && (
            <div className={styles.stockOverview}>
              <StockHistoryChart
                key={`history-${company.ticker}`}
                ticker={company.ticker}
                financialData={company.financial_data}
                historicalPrices={company.historical_prices}
              />
              <section className={styles.financialData} aria-labelledby="financial-data-heading">
                <h2 id="financial-data-heading">Financial data and ratios</h2>
                <dl className={styles.companyMetrics}>
                  {ratioFields.map(({ key, label, percentage }) => (
                    <Fragment key={key}>
                      <dt>{label}:</dt>
                      <dd>{formatRatio(company.ratios?.[key], percentage)}</dd>
                    </Fragment>
                  ))}
                  <dt>Backlog:</dt>
                  <dd>
                    {formatMillions(company.backlog)}
                  </dd>
                </dl>
              </section>
            </div>
          )}
        </>
      ) : (
        <p>{companiesLoading ? "Loading company details…" : ""}</p>
      )}
    </div>
  );
}
