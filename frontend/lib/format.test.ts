import { describe, expect, it } from "vitest";
import { formatMoney, formatSignedMoney } from "@/lib/format";

describe("formatMoney", () => {
  it("formats positive amounts without a sign", () => {
    expect(formatMoney(50)).toBe("50.00 zł");
  });

  it("formats negative amounts with a leading minus", () => {
    expect(formatMoney(-12.5)).toBe("-12.50 zł");
  });

  it("formats zero without a sign", () => {
    expect(formatMoney(0)).toBe("0.00 zł");
  });
});

describe("formatSignedMoney", () => {
  it("prefixes positive amounts with +", () => {
    expect(formatSignedMoney(50)).toBe("+50.00 zł");
  });

  it("prefixes negative amounts with -", () => {
    expect(formatSignedMoney(-50)).toBe("-50.00 zł");
  });

  it("shows zero with no sign", () => {
    expect(formatSignedMoney(0)).toBe("0.00 zł");
  });
});
