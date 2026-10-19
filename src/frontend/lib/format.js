const metricNumber = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2
});

const priceNumber = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

const ratioNumber = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

const percentageNumber = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 2
});

const rankNumber = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});

export function numericValue(value) {
  if (value === "inf") return Infinity;
  if (value === "-inf") return -Infinity;
  return typeof value === "number" && !Number.isNaN(value) ? value : null;
}

export function formatRatio(value, percentage = false) {
  const number = numericValue(value);
  if (number === null) return "—";
  return (percentage ? percentageNumber : ratioNumber).format(number);
}

export function formatRank(value) {
  const number = numericValue(value);
  if (number === null) return "—";
  return rankNumber.format(number);
}

export function formatMillions(value) {
  return Number.isFinite(value) ? `$${metricNumber.format(value)} million` : "—";
}

export function formatPrice(value) {
  return Number.isFinite(value) ? priceNumber.format(value) : "—";
}
