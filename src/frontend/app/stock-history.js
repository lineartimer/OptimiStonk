export function buildStockHistory(financialData = {}, historicalPrices = {}) {
  const quarters = new Set([
    ...Object.keys(financialData),
    ...Object.keys(historicalPrices)
  ]);

  return [...quarters].sort().map((quarter) => {
    const revenue = financialData[quarter]?.revenue;
    const price = historicalPrices[quarter];
    const [year, number] = quarter.split("/");

    return {
      quarter,
      label: `${year}/Q${number}`,
      // Preserve zero revenue; missing values must not become zeroes.
      revenue: Number.isFinite(revenue) ? revenue : null,
      price: Number.isFinite(price) ? price : null
    };
  });
}

export function getSeriesDomain(data, key) {
  let minimum = 0;
  let maximum = 0;

  for (const point of data) {
    const value = point[key];
    if (!Number.isFinite(value)) continue;
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }

  if (minimum === 0 && maximum === 0) return [0, 1];

  // Independent domains give both series the same proportional headroom,
  // even when revenue and price differ by several orders of magnitude.
  return [minimum * 1.1, maximum * 1.1];
}
