export type Locale = "en" | "ru";
export type Vars = Record<string, string | number>;
export type DictEntry = string | string[] | ((vars: Vars) => string);
export type Dictionary = Record<string, DictEntry>;
