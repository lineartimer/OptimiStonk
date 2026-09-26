import assert from "node:assert/strict";
import test from "node:test";
import { buildStockHistory, getSeriesDomain } from "./stock-history.mjs";

test("aligns and orders quarters without converting missing values to zero", () => {
  const data = buildStockHistory(
    { "2025/2": { revenue: 250 }, "2024/4": { revenue: 0 } },
    { "2025/1": 12.5, "2024/4": 10 }
  );

  assert.deepEqual(data, [
    { quarter: "2024/4", label: "Q4 2024", revenue: 0, price: 10 },
    { quarter: "2025/1", label: "Q1 2025", revenue: null, price: 12.5 },
    { quarter: "2025/2", label: "Q2 2025", revenue: 250, price: null }
  ]);
  assert.deepEqual(buildStockHistory(), []);
});

test("scales revenue and sub-dollar prices to comparable heights without changing their units", () => {
  const data = [{ revenue: 4000, price: 0.04 }, { revenue: 2000, price: 0.02 }];
  const revenueDomain = getSeriesDomain(data, "revenue");
  const priceDomain = getSeriesDomain(data, "price");

  assert.equal(revenueDomain[0], 0);
  assert.equal(priceDomain[0], 0);
  assert.ok(Math.abs(4000 / revenueDomain[1] - 0.04 / priceDomain[1]) < 1e-12);
  assert.ok(revenueDomain[1] > 4000);
  assert.ok(priceDomain[1] > 0.04);
});

test("keeps zero and missing series renderable and includes negative revenues", () => {
  assert.deepEqual(getSeriesDomain([], "revenue"), [0, 1]);
  assert.deepEqual(getSeriesDomain([{ revenue: 0 }, { revenue: null }], "revenue"), [0, 1]);
  const [minimum, maximum] = getSeriesDomain([{ revenue: -10 }, { revenue: 20 }], "revenue");
  assert.ok(minimum < -10);
  assert.ok(maximum > 20);
});

test("excludes non-finite values from chart data and axis domains", () => {
  const data = buildStockHistory({ "2025/1": { revenue: Infinity } }, { "2025/1": NaN });
  assert.equal(data[0].revenue, null);
  assert.equal(data[0].price, null);
  assert.deepEqual(getSeriesDomain([{ price: NaN }, { price: Infinity }], "price"), [0, 1]);
});
