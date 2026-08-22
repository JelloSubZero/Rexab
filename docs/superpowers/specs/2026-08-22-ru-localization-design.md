# Russian localization (RU/EN) — design

Date: 2026-08-22
Status: approved, pending implementation plan

## Problem

The entire frontend (`frontend/`) is English-only — every string is a
hardcoded literal inside JSX/TSX across ~30 page and component files. There
is no i18n infrastructure in the project (`package.json` has no `next-intl`,
`react-intl`, or similar; no `[locale]` route segment; no `middleware.ts` /
`proxy.ts`). The owner wants the app usable in Russian, with a manual
language switcher (not just a one-time translation), covering both the
authenticated app (dashboard, rooms, settings, login/register) and the
public marketing landing page (`app/page.tsx` + `components/landing/*`).

## Context that shapes the design

- The whole app is client-rendered: every page/component file starts with
  `"use client"`. `app/layout.tsx` is the only server component, and it's a
  thin wrapper (fonts, metadata, `AuthProvider`, `ToastProvider`). There is
  no server-side per-request locale to resolve, so URL-based locale routing
  (`/en/...`, `/ru/...`) would add real complexity (restructuring `app/`
  under a `[locale]` segment, a `proxy.ts` for detection/redirects) for no
  benefit this app needs — no per-locale SEO requirement was raised, and
  auth already gates most of the app.
- Next.js is v16.3.1, which **deprecated `middleware.ts` in favor of
  `proxy.ts`** (per `node_modules/next/dist/docs/.../proxy.md`). Avoiding
  the routing-based i18n approach also avoids this pitfall entirely.
- Only two strings in the app are count-dependent (Russian plural rules —
  one/few/many — don't map onto English's singular/plural):
  `app/(app)/rooms/[id]/page.tsx` ("N members") and `components/RoomCard.tsx`
  (same pattern). Everything else is static text.
- Existing `lib/format.ts` (money as `"... zł"`, dates via
  `toLocaleDateString(undefined, { day: "2-digit", month: "2-digit", year:
  "numeric" })`) is locale-agnostic in its *output* (numeric styles don't
  vary by locale) and orthogonal to language — currency/date format changes
  are out of scope; only interface text and pluralization are in scope.

## Approach

Given the app is 100% client-rendered and only two strings need
pluralization, a small hand-rolled i18n layer is proportionate — pulling in
`next-intl` (ICU message format, ~dozens of KB, ecosystem tooling) would be
solving a two-string problem with a general-purpose library, and its
idiomatic setup pushes toward the routing/middleware integration this app
explicitly doesn't need.

**Rejected alternative:** `next-intl` with `NextIntlClientProvider` only
(no routing) was considered. It would remove the need to hand-write
`pluralizeRu`, but adds a dependency, its own message-loading conventions,
and TypeScript message-key typing setup — overhead not justified by two
pluralized strings. Not chosen.

### Architecture

```
frontend/lib/i18n/
  dictionaries/
    en.ts       // Record<string, string | ((vars: Record<string, string|number>) => string)>
    ru.ts       // same shape
  pluralizeRu.ts
  LocaleProvider.tsx   // context + t() + locale + setLocale
  index.ts             // re-exports: useLocale, useTranslation (or similar)
```

- **Dictionary shape:** flat key → value map, where value is either a plain
  `string` or a `(vars) => string` function for interpolated/pluralized
  entries. `t(key, vars?)` looks up the entry; if it's a function, calls it
  with `vars`; otherwise returns it as-is (with `{placeholder}` substitution
  for the plain-string+vars case, e.g. greeting messages with a name).
  Missing-key fallback: return the key itself and `console.warn` in
  development, so a missing translation is visible but never crashes the
  UI.
- **Keys are namespaced by feature**, dot-separated, e.g.
  `"room.deleteButton"`, `"payment.addTitle"`, `"landing.hero.headline"`.
  This keeps the two dictionaries easy to diff against each other for
  parity (a follow-up lint/test, see Testing).
- **`pluralizeRu(n, [one, few, many])`**: implements the standard Russian
  plural-form rule (mod 10 / mod 100 based). Used inside `ru.ts` entries for
  the two count-dependent strings; the English dictionary uses the existing
  ternary logic inline in its own function value.
- **`LocaleProvider`** (client component, wraps `children` in
  `app/layout.tsx` alongside `AuthProvider`):
  - State: `locale: "en" | "ru" | null` (`null` = "not yet determined",
    client-only).
  - On mount: read `localStorage.getItem("rexab_locale")`; if absent, derive
    from `navigator.language.startsWith("ru") ? "ru" : "en"`. Persist
    whatever is resolved.
  - `setLocale(locale)`: updates state + `localStorage`.
  - While `locale === null` (i.e., before the client effect runs), render
    nothing (or a minimal blank shell) instead of English content, so
    Russian-browser users never see a flash of English. This mirrors the
    existing `AuthProvider`'s `isLoading` gating pattern already used
    app-wide, so it's a consistent, familiar shape in this codebase.
  - Exposes `t(key, vars?)` bound to the current locale's dictionary.

### Components

- `LanguageSwitcher` (new, small component): a two-state RU/EN toggle.
  Placed in `AppShell`'s top nav bar (authenticated chrome) and in
  `components/landing/Navbar.tsx` (public site). Calls `setLocale` from
  context.
- All ~30 page/feature files listed below get their literal strings
  replaced with `t("...")` calls. `components/ui/*` primitives
  (`Button`, `EmptyState`, `ConfirmDialog`, `Toast`, etc.) mostly already
  take text via props from callers and don't own copy themselves — callers
  pass translated strings through unchanged; only genuinely hardcoded
  defaults inside `ui/*` (if any are found during implementation) get their
  own keys.
- Files in scope (from repo scan):
  - `app/page.tsx`, `app/login/page.tsx`, `app/register/page.tsx`,
    `app/(app)/dashboard/page.tsx`, `app/(app)/layout.tsx`,
    `app/(app)/rooms/[id]/page.tsx`, `app/(app)/settings/page.tsx`
  - `components/AddPaymentDialog.tsx`, `AppShell.tsx`,
    `CreateRoomDialog.tsx`, `InviteDialog.tsx`, `JoinRoomDialog.tsx`,
    `MemberList.tsx`, `PaymentList.tsx`, `RoomCard.tsx`,
    `SettlementList.tsx`, `WhoOwesWhom.tsx`
  - `components/landing/*.tsx` (Hero, HeroDashboard, Features, FinalCTA,
    Footer, HowItWorks, InteractiveDemo, Navbar, ProblemSection,
    ProductShowcase, TrustSection, UseCases, plus their mock data in
    `mock-data.ts` where it's display copy, not just structural data)
  - `app/layout.tsx` metadata (`title`/`description`) is server-rendered
    and has no client locale available at that point — out of scope, stays
    English (standard practice for a single canonical `<meta>` without
    locale routing).

### Data flow / persistence

1. First visit: `LocaleProvider` mounts → checks `localStorage` → falls back
   to `navigator.language` → sets `locale` + persists it.
2. User toggles via `LanguageSwitcher` → `setLocale` updates context state +
   `localStorage` → every `t()` call across the tree re-renders with new
   strings (standard context re-render, no page reload needed).
3. Locale is a client-only preference; it does not sync to the backend or
   affect API calls (e.g. `payer_name` from the API stays whatever the DB
   has — user-entered names aren't translated, only interface chrome is).

### Error handling

- Missing translation key → fallback to the key string itself +
  dev-only console warning (never a blank string or crash).
- `navigator` access is guarded (only read inside the client effect, never
  during SSR) to avoid hydration mismatches.

### Testing

- Unit test for `pluralizeRu`: boundary cases `1→one, 2→few, 4→few, 5→many,
  11→many, 21→one, 22→few, 25→many, 0→many`.
- Unit test for `LocaleProvider`/`useTranslation`: browser-language
  detection (`ru-RU` → `ru`, `en-US` → `en`, unrecognized → `en`),
  `localStorage` persistence and read-back, manual `setLocale` override.
- A small parity test asserting `en.ts` and `ru.ts` export the exact same
  set of keys (catches drift as new keys are added later).
- Manual verification in the browser (per this project's UI-change
  workflow): toggle language on the landing page and inside the app, check
  for no hydration warnings in the console, confirm the two pluralized
  strings render correctly for a few member counts.

## Out of scope

- URL-based locale routing / `proxy.ts` / per-locale SEO metadata.
- Translating user-generated content (payer names, room names, payment
  descriptions) — only static interface copy.
- Currency/date formatting changes — `lib/format.ts` is untouched.
- Adding more languages beyond EN/RU (the dictionary structure doesn't
  preclude it later, but nothing is built for it now).
