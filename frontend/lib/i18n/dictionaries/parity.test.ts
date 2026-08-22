import { describe, expect, it } from "vitest";
import { en } from "@/lib/i18n/dictionaries/en";
import { ru } from "@/lib/i18n/dictionaries/ru";

describe("translation dictionary parity", () => {
  it("en and ru export exactly the same set of keys", () => {
    expect(Object.keys(ru).sort()).toEqual(Object.keys(en).sort());
  });

  it("every dictionary value is a string, string[], or function", () => {
    for (const dict of [en, ru]) {
      for (const [key, value] of Object.entries(dict)) {
        const ok =
          typeof value === "string" ||
          Array.isArray(value) ||
          typeof value === "function";
        expect(ok, `key "${key}" has an invalid value type`).toBe(true);
      }
    }
  });
});
