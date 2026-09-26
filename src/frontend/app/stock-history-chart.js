"use client";

import { useId, useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { buildStockHistory, getSeriesDomain } from "./stock-history.js";
import styles from "./page.module.css";

const revenueColor = "#2563eb";
const priceColor = "#dc2626";
const axisNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2
});
const revenueNumber = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const priceNumber = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

function formatTooltip(value, name, item) {
  return [
    item.dataKey === "revenue"
      ? `$${revenueNumber.format(value)} million`
      : priceNumber.format(value),
    name
  ];
}

export default function StockHistoryChart({ ticker, financialData, historicalPrices }) {
  const headingId = useId();
  const data = useMemo(
    () => buildStockHistory(financialData, historicalPrices),
    [financialData, historicalPrices]
  );
  const hasRevenue = data.some(({ revenue }) => revenue !== null);
  const hasPrices = data.some(({ price }) => price !== null);

  return (
    <section className={styles.historyChart} aria-labelledby={headingId}>
      <h2 id={headingId}>Quarterly revenue and stock price</h2>
      {!hasRevenue && !hasPrices ? (
        <p>No quarterly revenue or price history available.</p>
      ) : (
        <>
          {(!hasRevenue || !hasPrices) && (
            <p>{hasRevenue ? "Stock price history" : "Quarterly revenue"} is unavailable.</p>
          )}
          <div className={styles.chartScroll}>
            <div className={styles.chartCanvas}>
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <ComposedChart
                  data={data}
                  margin={{ top: 12, right: 12, bottom: 8, left: 12 }}
                  accessibilityLayer
                  title={`${ticker} quarterly revenue and stock price`}
                  desc="Blue bars show revenue in millions of US dollars on the left axis. The red line shows quarter-end stock prices in US dollars on the right axis. Each axis is scaled independently."
                >
                  <CartesianGrid yAxisId="revenue" stroke="#d0dce5" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 12, fill: "#122a4a" }}
                    tickLine={false}
                    minTickGap={24}
                    interval="preserveStartEnd"
                    height={40}
                  />
                  <YAxis
                    yAxisId="revenue"
                    orientation="left"
                    domain={getSeriesDomain(data, "revenue")}
                    tickFormatter={(value) => axisNumber.format(value)}
                    tick={{ fontSize: 12, fill: revenueColor }}
                    stroke={revenueColor}
                    tickLine={false}
                    width={80}
                    label={{ value: "Revenue ($M)", angle: -90, position: "insideLeft", fill: revenueColor }}
                  />
                  <YAxis
                    yAxisId="price"
                    orientation="right"
                    domain={getSeriesDomain(data, "price")}
                    tickFormatter={(value) => axisNumber.format(value)}
                    tick={{ fontSize: 12, fill: priceColor }}
                    stroke={priceColor}
                    tickLine={false}
                    width={80}
                    label={{ value: "Price ($)", angle: 90, position: "insideRight", fill: priceColor }}
                  />
                  <Tooltip
                    formatter={formatTooltip}
                    cursor={{ fill: "#122a4a", fillOpacity: 0.04 }}
                    contentStyle={{ borderColor: "#d0dce5", borderRadius: 4 }}
                    labelStyle={{ color: "#122a4a", fontWeight: "bold" }}
                  />
                  <Legend wrapperStyle={{ paddingTop: 8 }} />
                  <Bar
                    yAxisId="revenue"
                    dataKey="revenue"
                    name="Revenue ($M)"
                    fill={revenueColor}
                    maxBarSize={40}
                    isAnimationActive={false}
                  />
                  <Line
                    yAxisId="price"
                    dataKey="price"
                    name="Quarter-end price ($)"
                    type="linear"
                    stroke={priceColor}
                    strokeWidth={2}
                    dot={{ r: 3, fill: priceColor }}
                    activeDot={{ r: 5 }}
                    connectNulls={false}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
