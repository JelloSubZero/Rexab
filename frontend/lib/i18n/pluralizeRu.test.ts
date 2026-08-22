import { describe, expect, it } from "vitest";
import { pluralizeRu } from "@/lib/i18n/pluralizeRu";

describe("pluralizeRu", () => {
  const forms: [string, string, string] = ["one", "few", "many"];

  it.each([
    [0, "many"],
    [1, "one"],
    [2, "few"],
    [4, "few"],
    [5, "many"],
    [11, "many"],
    [12, "many"],
    [14, "many"],
    [21, "one"],
    [22, "few"],
    [24, "few"],
    [25, "many"],
    [101, "one"],
    [111, "many"],
  ])("pluralizeRu(%i, ...) returns the %s form", (n, expected) => {
    expect(pluralizeRu(n, forms)).toBe(expected);
  });
});
