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

  it("function-valued and array-valued keys have matching shapes across locales", () => {
    for (const key of Object.keys(en)) {
      const enValue = en[key];
      const ruValue = ru[key];

      expect(typeof ruValue, `key "${key}": function/string mismatch`).toBe(
        typeof enValue,
      );

      if (Array.isArray(enValue)) {
        expect(Array.isArray(ruValue), `key "${key}": expected an array in ru`).toBe(true);
        expect((ruValue as string[]).length, `key "${key}": array length mismatch`).toBe(
          enValue.length,
        );
      }
    }
  });
});
