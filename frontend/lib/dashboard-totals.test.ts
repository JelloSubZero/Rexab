import { describe, expect, it } from "vitest";
import { aggregateDashboardTotals } from "@/lib/dashboard-totals";

describe("aggregateDashboardTotals", () => {
  it("sums positive balances into youAreOwed and negative into youOwe", () => {
    const totals = aggregateDashboardTotals([
      { balance: 50 },
      { balance: -20 },
      { balance: -5 },
    ]);

    expect(totals.youAreOwed).toBe(50);
    expect(totals.youOwe).toBe(25);
    expect(totals.netBalance).toBe(25);
  });

  it("ignores rooms whose balance failed to load instead of treating them as zero", () => {
    const totals = aggregateDashboardTotals([
      { balance: 100 },
      { balance: null },
    ]);

    expect(totals.youAreOwed).toBe(100);
    expect(totals.youOwe).toBe(0);
  });

  it("returns all zeros for an empty room list", () => {
    expect(aggregateDashboardTotals([])).toEqual({
      youOwe: 0,
      youAreOwed: 0,
      netBalance: 0,
    });
  });

  it("treats a zero balance as neither owed nor owing", () => {
    const totals = aggregateDashboardTotals([{ balance: 0 }]);

    expect(totals.youOwe).toBe(0);
    expect(totals.youAreOwed).toBe(0);
    expect(totals.netBalance).toBe(0);
  });
});
