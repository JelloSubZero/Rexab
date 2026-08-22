# RU/EN Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a manual RU/EN language switcher covering the entire frontend (authenticated app + public landing page), with no new npm dependency.

**Architecture:** A hand-rolled i18n layer — flat dictionaries (`en.ts`/`ru.ts`) keyed by dot-separated strings, a `LocaleProvider` React context exposing `t()`/`tList()`, browser-language detection with `localStorage` persistence, and a `LanguageSwitcher` toggle. Every page/component file with hardcoded copy is rewired to call `t("key")` instead of the literal string. No URL routing, no `proxy.ts`.

**Tech Stack:** Next.js 16.3.1 (App Router, 100% client components), React 19, Vitest + Testing Library (existing test setup).

**Spec:** [docs/superpowers/specs/2026-08-22-ru-localization-design.md](../specs/2026-08-22-ru-localization-design.md)

## Global Constraints

- No new npm dependency (no `next-intl`/`react-intl`) — spec explicitly rejected this.
- No URL-based locale routing, no `proxy.ts`/`middleware.ts` — spec explicitly rejected this.
- `localStorage` key is `"rexab_locale"`, values `"en" | "ru"`.
- Locale detection on first visit: `navigator.language` starts with `"ru"` → `"ru"`, else `"en"`.
- Missing dictionary key → return the key itself + `console.warn` in dev (never crash, never blank).
- Currency/date formatting in `lib/format.ts` stays untouched — out of scope.
- User-generated content (names, room names typed by users, payment descriptions typed by users) is never translated — only static interface copy and the landing page's fixed demo data.
- After every task: `npm test` (from `frontend/`) must pass before committing.

---

## Task 1: `pluralizeRu` utility

**Files:**
- Create: `frontend/lib/i18n/pluralizeRu.ts`
- Test: `frontend/lib/i18n/pluralizeRu.test.ts`

**Interfaces:**
- Produces: `pluralizeRu(n: number, forms: [string, string, string]): string` — `forms` is `[one, few, many]`. Used by later tasks for Russian member-count strings.

- [ ] **Step 1: Write the failing test**

```ts
// frontend/lib/i18n/pluralizeRu.test.ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `npx vitest run lib/i18n/pluralizeRu.test.ts`
Expected: FAIL — `Cannot find module '@/lib/i18n/pluralizeRu'`.

- [ ] **Step 3: Write minimal implementation**

```ts
// frontend/lib/i18n/pluralizeRu.ts
export function pluralizeRu(
  n: number,
  [one, few, many]: [string, string, string],
): string {
  const mod10 = n % 10;
  const mod100 = n % 100;

  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run lib/i18n/pluralizeRu.test.ts`
Expected: PASS (14 cases).

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/i18n/pluralizeRu.ts frontend/lib/i18n/pluralizeRu.test.ts
git commit -m "feat(i18n): add pluralizeRu for Russian plural forms"
```

---

## Task 2: i18n types + full EN/RU dictionaries + parity test

**Files:**
- Create: `frontend/lib/i18n/types.ts`
- Create: `frontend/lib/i18n/dictionaries/en.ts`
- Create: `frontend/lib/i18n/dictionaries/ru.ts`
- Test: `frontend/lib/i18n/dictionaries/parity.test.ts`

**Interfaces:**
- Consumes: `pluralizeRu` from Task 1.
- Produces: `type Locale = "en" | "ru"`, `type Vars = Record<string, string | number>`, `type DictEntry = string | string[] | ((vars: Vars) => string)`, `type Dictionary = Record<string, DictEntry>`, and the `en`/`ru` dictionary objects (identical key sets) consumed by every later task via `t("...")`/`tList("...")`.

- [ ] **Step 1: Write the failing parity test**

```ts
// frontend/lib/i18n/dictionaries/parity.test.ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run lib/i18n/dictionaries/parity.test.ts`
Expected: FAIL — `Cannot find module '@/lib/i18n/dictionaries/en'`.

- [ ] **Step 3: Write the shared types**

```ts
// frontend/lib/i18n/types.ts
export type Locale = "en" | "ru";
export type Vars = Record<string, string | number>;
export type DictEntry = string | string[] | ((vars: Vars) => string);
export type Dictionary = Record<string, DictEntry>;
```

- [ ] **Step 4: Write the English dictionary**

```ts
// frontend/lib/i18n/dictionaries/en.ts
import type { Dictionary } from "@/lib/i18n/types";

export const en: Dictionary = {
  // common
  "common.cancel": "Cancel",
  "common.confirm": "Confirm",
  "common.close": "Close",
  "common.paidWord": "paid",

  // nav
  "nav.dashboard": "Dashboard",
  "nav.settings": "Settings",
  "nav.logout": "Log out",

  // auth - login
  "auth.login.title": "Welcome back",
  "auth.login.subtitle": "Log in to see your rooms and balances.",
  "auth.login.emailLabel": "Email",
  "auth.login.passwordLabel": "Password",
  "auth.login.submit": "Log in",
  "auth.login.noAccount": "No account?",
  "auth.login.createOne": "Create one",

  // auth - register
  "auth.register.title": "Create your account",
  "auth.register.subtitle": "Split bills with friends and roommates.",
  "auth.register.nameLabel": "Name",
  "auth.register.emailLabel": "Email",
  "auth.register.passwordLabel": "Password",
  "auth.register.passwordTooShort": "Password must be at least 8 characters.",
  "auth.register.submit": "Create account",
  "auth.register.haveAccount": "Already have an account?",
  "auth.register.logIn": "Log in",

  // shared stat labels (dashboard + room page + landing demo)
  "stats.youOwe": "You owe",
  "stats.owedToYou": "Owed to you",
  "stats.balance": "Balance",

  // dashboard
  "dashboard.greeting": ({ name }) => `Good to see you, ${name}`,
  "dashboard.subtitle": "Here's what's happening in your rooms.",
  "dashboard.yourRooms": "Your rooms",
  "dashboard.noRoomsTitle": "No rooms yet",
  "dashboard.noRoomsDescription":
    "Create a room to start splitting expenses, or join one with an invite code.",

  // shared room actions
  "room.actions.create": "Create room",
  "room.actions.join": "Join room",
  "room.actions.addPayment": "Add payment",
  "room.actions.addMember": "Add member",
  "room.actions.settleUp": "Settle up",
  "room.actions.confirmPayment": "Confirm payment",
  "room.actions.remove": "Remove",
  "room.actions.copyCode": "Copy code",
  "room.actions.copied": "Copied!",

  // room card
  "room.card.unnamedRoom": ({ code }) => `Room ${code}`,
  "room.card.memberCount": ({ count }) =>
    `${count} ${count === 1 ? "member" : "members"}`,

  // dialogs
  "dialog.createRoom.nameLabel": "Room name",
  "dialog.createRoom.namePlaceholder": "Apartment",
  "dialog.joinRoom.title": "Join a room",
  "dialog.joinRoom.codeLabel": "Invitation code",
  "dialog.addPayment.amountLabel": "Amount",
  "dialog.addPayment.amountPlaceholder": "100",
  "dialog.addPayment.descriptionLabel": "Description",
  "dialog.addPayment.descriptionPlaceholder": "Dinner",
  "dialog.addPayment.paidByLabel": "Paid by",
  "dialog.addPayment.youSuffix": " (you)",
  "dialog.addPayment.invalidAmount": "Enter a valid amount.",
  "dialog.invite.title": "Invite to room",
  "dialog.invite.description": "Share this code with friends so they can join.",

  // room page
  "room.page.deleteRoom": "Delete room",
  "room.page.leaveRoom": "Leave room",
  "room.page.deleteConfirmTitle": "Delete this room?",
  "room.page.deleteConfirmDescription":
    "This permanently deletes the room and all its payments, receipts and settlements. This cannot be undone.",
  "room.page.leaveConfirmTitle": "Leave this room?",
  "room.page.leaveConfirmDescription": "You can rejoin later with the invite code.",
  "room.page.requestSettlementTitle": "Request settlement?",
  "room.page.requestSettlementDescription": ({ amount }) =>
    `Mark ${amount} as being settled between these two members. The receiver will need to confirm.`,
  "room.page.requestSettlementConfirm": "Request settlement",
  "room.page.confirmPaymentTitle": "Confirm payment?",
  "room.page.confirmPaymentDescription":
    "Did you actually receive this payment? Confirming will mark the debt as settled.",
  "room.page.removeMemberTitle": "Remove member?",
  "room.page.removeMemberDescription": ({ name }) =>
    `${name} will lose access to this room.`,

  // payment list
  "payment.list.title": "Payments",
  "payment.list.emptyTitle": "No payments yet",
  "payment.list.emptyDescription": "Add the first expense for this room.",
  "payment.list.fallbackDescription": "Expense",

  // member list
  "member.list.title": "Members",
  "member.list.ownerLabel": "Owner",

  // settlement list
  "settlement.list.title": "Settlements",
  "settlement.list.emptyTitle": "No settlements yet",
  "settlement.list.owesWord": "owes",
  "settlement.list.waitingConfirmation": "Waiting for confirmation",

  // who owes whom
  "whoOwesWhom.title": "Who owes whom",
  "whoOwesWhom.emptyTitle": "Everyone is settled up.",

  // settings
  "settings.noEmail": "No email on this account",
  "settings.linkedTelegram": ({ id }) => `Linked to Telegram (id ${id})`,

  // landing nav
  "landing.nav.howItWorks": "How it works",
  "landing.nav.features": "Features",
  "landing.nav.useCases": "Use cases",
  "landing.nav.login": "Login",
  "landing.nav.openMenu": "Open menu",
  "landing.nav.closeMenu": "Close menu",
  "landing.cta.getStarted": "Get started",

  // landing hero
  "landing.hero.badge": "Shared expenses, simplified",
  "landing.hero.headline": "Manage shared expenses",
  "landing.hero.headlineSuffix": "without the",
  "landing.hero.headlineAccent": "headache.",
  "landing.hero.subtitle":
    "Rexab makes it simple to track expenses, split costs and settle debts with your roommates, friends and travel groups.",
  "landing.hero.seeHowItWorks": "See how it works",

  // landing hero dashboard / shared demo data
  "landing.demo.roomName": "Apartment",
  "landing.demo.you": "You",
  "landing.heroDashboard.yourBalance": "Your balance",
  "landing.heroDashboard.youAreOwed": "You are owed",
  "landing.heroDashboard.recentPayment": "Recent payment",
  "landing.heroDashboard.settlementConfirmed": "✓ Settlement confirmed",

  // landing demo payments
  "landing.demo.payments.dinner": "Dinner",
  "landing.demo.payments.groceries": "Groceries",
  "landing.demo.payments.internet": "Internet",
  "landing.demo.payments.utilities": "Utilities",

  // landing demo statuses
  "landing.demo.status.active": "Active",
  "landing.demo.status.confirmed": "Confirmed",
  "landing.demo.status.pending": "Pending",

  // landing problem section
  "landing.problem.title": "Shared expenses shouldn't be complicated.",
  "landing.problem.subtitle":
    "You paid for dinner. Someone bought groceries. Another person paid the rent. And now — who owes whom?",
  "landing.problem.withoutRexab": "Without Rexab",
  "landing.problem.withRexab": "With Rexab",

  // landing how it works
  "landing.howItWorks.title": "How Rexab works.",
  "landing.howItWorks.subtitle": "Three simple steps. No spreadsheets. No calculations.",
  "landing.howItWorks.step1.title": "Create a room",
  "landing.howItWorks.step1.description": "Create a space for your apartment, trip or group.",
  "landing.howItWorks.step2.title": "Add expenses",
  "landing.howItWorks.step2.description": "Record who paid and who should share the cost.",
  "landing.howItWorks.step3.title": "Settle up",
  "landing.howItWorks.step3.description": "Rexab calculates who owes whom and tracks repayments.",

  // landing showcase
  "landing.showcase.title": "Stop doing math in group chats.",
  "landing.showcase.subtitle":
    "Rexab keeps every shared expense, balance and settlement in one place — so no one has to scroll back through messages to remember who paid for what.",
  "landing.showcase.totalExpenses": "Total expenses",

  // landing features
  "landing.features.title": "Everything your group needs.",
  "landing.features.shared.title": "Shared expenses",
  "landing.features.shared.description":
    "Track every expense in one place, with who paid and who owes what always visible.",
  "landing.features.group.title": "Group management",
  "landing.features.group.description": "Manage members and permissions easily.",
  "landing.features.settlements.title": "Easy settlements",
  "landing.features.settlements.description": "Keep track of who has paid you back.",
  "landing.features.overview.title": "Clear overview",
  "landing.features.overview.description":
    "See balances and debts instantly, without digging through chat history.",

  // landing use cases
  "landing.useCases.title": "Wherever money is shared.",
  "landing.useCases.roommates.title": "Roommates",
  "landing.useCases.roommates.items": ["Rent", "Groceries", "Utilities", "Internet"],
  "landing.useCases.trips.title": "Trips",
  "landing.useCases.trips.items": ["Hotels", "Food", "Transport", "Tickets"],
  "landing.useCases.groups.title": "Groups",
  "landing.useCases.groups.items": ["Events", "Parties", "Projects", "Activities"],

  // landing trust
  "landing.trust.title": "Built around clarity.",
  "landing.trust.points": [
    "Clear balances",
    "Transparent settlements",
    "Permission-based actions",
    "One source of truth",
    "Simple group management",
  ],
  "landing.trust.footnote":
    "Every balance-changing action goes through a permission check on the server — not the client — before it's applied.",

  // landing interactive demo
  "landing.demo.title": "See your money clearly.",
  "landing.demo.subtitle": "Everything important at a glance.",
  "landing.demo.tabs.expenses": "Expenses",

  // landing final CTA
  "landing.finalCta.title": "Ready to stop doing the math?",
  "landing.finalCta.subtitle": "Create your first room and keep shared expenses under control.",

  // landing footer
  "landing.footer.tagline": "Shared expenses. Simplified.",
  "landing.footer.columns.product": "Product",
  "landing.footer.columns.resources": "Resources",
  "landing.footer.columns.company": "Company",
  "landing.footer.columns.legal": "Legal",
  "landing.footer.links.help": "Help",
  "landing.footer.links.documentation": "Documentation",
  "landing.footer.links.about": "About",
  "landing.footer.links.contact": "Contact",
  "landing.footer.links.privacy": "Privacy",
  "landing.footer.links.terms": "Terms",
};
```

- [ ] **Step 5: Write the Russian dictionary**

```ts
// frontend/lib/i18n/dictionaries/ru.ts
import type { Dictionary } from "@/lib/i18n/types";
import { pluralizeRu } from "@/lib/i18n/pluralizeRu";

export const ru: Dictionary = {
  "common.cancel": "Отмена",
  "common.confirm": "Подтвердить",
  "common.close": "Закрыть",
  "common.paidWord": "оплатил(а)",

  "nav.dashboard": "Дашборд",
  "nav.settings": "Настройки",
  "nav.logout": "Выйти",

  "auth.login.title": "С возвращением",
  "auth.login.subtitle": "Войдите, чтобы увидеть свои комнаты и балансы.",
  "auth.login.emailLabel": "Email",
  "auth.login.passwordLabel": "Пароль",
  "auth.login.submit": "Войти",
  "auth.login.noAccount": "Нет аккаунта?",
  "auth.login.createOne": "Создать",

  "auth.register.title": "Создайте аккаунт",
  "auth.register.subtitle": "Делите счета с друзьями и соседями.",
  "auth.register.nameLabel": "Имя",
  "auth.register.emailLabel": "Email",
  "auth.register.passwordLabel": "Пароль",
  "auth.register.passwordTooShort": "Пароль должен содержать не менее 8 символов.",
  "auth.register.submit": "Создать аккаунт",
  "auth.register.haveAccount": "Уже есть аккаунт?",
  "auth.register.logIn": "Войти",

  "stats.youOwe": "Вы должны",
  "stats.owedToYou": "Вам должны",
  "stats.balance": "Баланс",

  "dashboard.greeting": ({ name }) => `Рады видеть вас, ${name}`,
  "dashboard.subtitle": "Вот что происходит в ваших комнатах.",
  "dashboard.yourRooms": "Ваши комнаты",
  "dashboard.noRoomsTitle": "Пока нет комнат",
  "dashboard.noRoomsDescription":
    "Создайте комнату, чтобы начать делить расходы, или присоединитесь по коду приглашения.",

  "room.actions.create": "Создать комнату",
  "room.actions.join": "Присоединиться",
  "room.actions.addPayment": "Добавить платёж",
  "room.actions.addMember": "Добавить участника",
  "room.actions.settleUp": "Рассчитаться",
  "room.actions.confirmPayment": "Подтвердить оплату",
  "room.actions.remove": "Удалить",
  "room.actions.copyCode": "Скопировать код",
  "room.actions.copied": "Скопировано!",

  "room.card.unnamedRoom": ({ code }) => `Комната ${code}`,
  "room.card.memberCount": ({ count }) =>
    `${count} ${pluralizeRu(Number(count), ["участник", "участника", "участников"])}`,

  "dialog.createRoom.nameLabel": "Название комнаты",
  "dialog.createRoom.namePlaceholder": "Квартира",
  "dialog.joinRoom.title": "Присоединиться к комнате",
  "dialog.joinRoom.codeLabel": "Код приглашения",
  "dialog.addPayment.amountLabel": "Сумма",
  "dialog.addPayment.amountPlaceholder": "100",
  "dialog.addPayment.descriptionLabel": "Описание",
  "dialog.addPayment.descriptionPlaceholder": "Ужин",
  "dialog.addPayment.paidByLabel": "Кто заплатил",
  "dialog.addPayment.youSuffix": " (вы)",
  "dialog.addPayment.invalidAmount": "Введите корректную сумму.",
  "dialog.invite.title": "Пригласить в комнату",
  "dialog.invite.description": "Поделитесь этим кодом с друзьями, чтобы они могли присоединиться.",

  "room.page.deleteRoom": "Удалить комнату",
  "room.page.leaveRoom": "Покинуть комнату",
  "room.page.deleteConfirmTitle": "Удалить эту комнату?",
  "room.page.deleteConfirmDescription":
    "Это навсегда удалит комнату, все платежи, чеки и расчёты. Отменить это действие будет невозможно.",
  "room.page.leaveConfirmTitle": "Покинуть эту комнату?",
  "room.page.leaveConfirmDescription": "Вы сможете вернуться позже по коду приглашения.",
  "room.page.requestSettlementTitle": "Запросить расчёт?",
  "room.page.requestSettlementDescription": ({ amount }) =>
    `Отметить ${amount} как погашенные между этими участниками. Получателю нужно будет подтвердить.`,
  "room.page.requestSettlementConfirm": "Запросить расчёт",
  "room.page.confirmPaymentTitle": "Подтвердить оплату?",
  "room.page.confirmPaymentDescription":
    "Вы действительно получили этот платёж? Подтверждение отметит долг как погашенный.",
  "room.page.removeMemberTitle": "Удалить участника?",
  "room.page.removeMemberDescription": ({ name }) =>
    `${name} потеряет доступ к этой комнате.`,

  "payment.list.title": "Платежи",
  "payment.list.emptyTitle": "Платежей пока нет",
  "payment.list.emptyDescription": "Добавьте первый расход для этой комнаты.",
  "payment.list.fallbackDescription": "Расход",

  "member.list.title": "Участники",
  "member.list.ownerLabel": "Владелец",

  "settlement.list.title": "Расчёты",
  "settlement.list.emptyTitle": "Расчётов пока нет",
  "settlement.list.owesWord": "должен(-на)",
  "settlement.list.waitingConfirmation": "Ожидает подтверждения",

  "whoOwesWhom.title": "Кто кому должен",
  "whoOwesWhom.emptyTitle": "Все расчёты завершены.",

  "settings.noEmail": "На аккаунте нет email",
  "settings.linkedTelegram": ({ id }) => `Привязан Telegram (id ${id})`,

  "landing.nav.howItWorks": "Как это работает",
  "landing.nav.features": "Возможности",
  "landing.nav.useCases": "Сценарии использования",
  "landing.nav.login": "Войти",
  "landing.nav.openMenu": "Открыть меню",
  "landing.nav.closeMenu": "Закрыть меню",
  "landing.cta.getStarted": "Начать",

  "landing.hero.badge": "Общие расходы — просто",
  "landing.hero.headline": "Управляйте общими расходами",
  "landing.hero.headlineSuffix": "без",
  "landing.hero.headlineAccent": "головной боли.",
  "landing.hero.subtitle":
    "Rexab упрощает учёт расходов, разделение затрат и расчёты с соседями, друзьями и попутчиками.",
  "landing.hero.seeHowItWorks": "Посмотреть, как это работает",

  "landing.demo.roomName": "Квартира",
  "landing.demo.you": "Вы",
  "landing.heroDashboard.yourBalance": "Ваш баланс",
  "landing.heroDashboard.youAreOwed": "Вам должны",
  "landing.heroDashboard.recentPayment": "Последний платёж",
  "landing.heroDashboard.settlementConfirmed": "✓ Расчёт подтверждён",

  "landing.demo.payments.dinner": "Ужин",
  "landing.demo.payments.groceries": "Продукты",
  "landing.demo.payments.internet": "Интернет",
  "landing.demo.payments.utilities": "Коммунальные услуги",

  "landing.demo.status.active": "Активна",
  "landing.demo.status.confirmed": "Подтверждено",
  "landing.demo.status.pending": "Ожидает",

  "landing.problem.title": "Общие расходы не должны быть сложными.",
  "landing.problem.subtitle":
    "Вы заплатили за ужин. Кто-то купил продукты. Другой человек оплатил аренду. И теперь — кто кому должен?",
  "landing.problem.withoutRexab": "Без Rexab",
  "landing.problem.withRexab": "С Rexab",

  "landing.howItWorks.title": "Как работает Rexab.",
  "landing.howItWorks.subtitle": "Три простых шага. Никаких таблиц. Никаких расчётов вручную.",
  "landing.howItWorks.step1.title": "Создайте комнату",
  "landing.howItWorks.step1.description": "Создайте пространство для квартиры, поездки или группы.",
  "landing.howItWorks.step2.title": "Добавляйте расходы",
  "landing.howItWorks.step2.description": "Записывайте, кто платил и кто должен разделить расход.",
  "landing.howItWorks.step3.title": "Рассчитайтесь",
  "landing.howItWorks.step3.description": "Rexab рассчитывает, кто кому должен, и отслеживает выплаты.",

  "landing.showcase.title": "Хватит считать в переписках.",
  "landing.showcase.subtitle":
    "Rexab хранит все общие расходы, балансы и расчёты в одном месте — никому не придётся листать переписку, чтобы вспомнить, кто за что платил.",
  "landing.showcase.totalExpenses": "Общие расходы",

  "landing.features.title": "Всё, что нужно вашей группе.",
  "landing.features.shared.title": "Общие расходы",
  "landing.features.shared.description":
    "Отслеживайте все расходы в одном месте — всегда видно, кто платил и кто сколько должен.",
  "landing.features.group.title": "Управление группой",
  "landing.features.group.description": "Легко управляйте участниками и правами доступа.",
  "landing.features.settlements.title": "Простые расчёты",
  "landing.features.settlements.description": "Следите за тем, кто вам уже вернул деньги.",
  "landing.features.overview.title": "Наглядный обзор",
  "landing.features.overview.description":
    "Мгновенно видьте балансы и долги, не копаясь в истории переписки.",

  "landing.useCases.title": "Везде, где делят деньги.",
  "landing.useCases.roommates.title": "Соседи",
  "landing.useCases.roommates.items": ["Аренда", "Продукты", "Коммунальные услуги", "Интернет"],
  "landing.useCases.trips.title": "Поездки",
  "landing.useCases.trips.items": ["Отели", "Еда", "Транспорт", "Билеты"],
  "landing.useCases.groups.title": "Группы",
  "landing.useCases.groups.items": ["Мероприятия", "Вечеринки", "Проекты", "Активности"],

  "landing.trust.title": "Построено вокруг ясности.",
  "landing.trust.points": [
    "Прозрачные балансы",
    "Прозрачные расчёты",
    "Действия на основе прав доступа",
    "Единый источник правды",
    "Простое управление группой",
  ],
  "landing.trust.footnote":
    "Каждое действие, влияющее на баланс, проходит проверку прав на сервере — а не на клиенте — прежде чем применяется.",

  "landing.demo.title": "Ваши финансы — как на ладони.",
  "landing.demo.subtitle": "Всё важное — с первого взгляда.",
  "landing.demo.tabs.expenses": "Расходы",

  "landing.finalCta.title": "Готовы перестать считать вручную?",
  "landing.finalCta.subtitle": "Создайте первую комнату и держите общие расходы под контролем.",

  "landing.footer.tagline": "Общие расходы. Просто.",
  "landing.footer.columns.product": "Продукт",
  "landing.footer.columns.resources": "Ресурсы",
  "landing.footer.columns.company": "Компания",
  "landing.footer.columns.legal": "Юридическая информация",
  "landing.footer.links.help": "Помощь",
  "landing.footer.links.documentation": "Документация",
  "landing.footer.links.about": "О нас",
  "landing.footer.links.contact": "Контакты",
  "landing.footer.links.privacy": "Конфиденциальность",
  "landing.footer.links.terms": "Условия",
};
```

- [ ] **Step 6: Run test to verify it passes**

Run: `npx vitest run lib/i18n/dictionaries/parity.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add frontend/lib/i18n/types.ts frontend/lib/i18n/dictionaries/
git commit -m "feat(i18n): add EN/RU translation dictionaries with parity test"
```

---

## Task 3: `LocaleProvider` + `useTranslation`

**Files:**
- Create: `frontend/lib/i18n/LocaleProvider.tsx`
- Test: `frontend/lib/i18n/LocaleProvider.test.tsx`

**Interfaces:**
- Consumes: `en`, `ru` from Task 2; `Locale`, `Vars` types from Task 2.
- Produces: `LocaleProvider({ children }): JSX.Element | null`, `useTranslation(): { locale: Locale; setLocale: (l: Locale) => void; t: (key: string, vars?: Vars) => string; tList: (key: string) => string[] }`, `detectLocale(): Locale`. `localStorage` key `"rexab_locale"`.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/lib/i18n/LocaleProvider.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LocaleProvider, useTranslation } from "@/lib/i18n/LocaleProvider";

function TestConsumer() {
  const { locale, setLocale, t } = useTranslation();
  return (
    <div>
      <p>locale: {locale}</p>
      <p>{t("common.cancel")}</p>
      <button onClick={() => setLocale("ru")}>switch to ru</button>
    </div>
  );
}

function MissingKeyConsumer() {
  const { t } = useTranslation();
  return <p>{t("nonexistent.key")}</p>;
}

function setBrowserLanguage(language: string) {
  Object.defineProperty(window.navigator, "language", {
    value: language,
    configurable: true,
  });
}

describe("LocaleProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    setBrowserLanguage("en-US");
  });

  it("detects Russian from the browser language when nothing is stored", () => {
    setBrowserLanguage("ru-RU");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
    expect(screen.getByText("Отмена")).toBeInTheDocument();
  });

  it("defaults to English for a non-Russian browser language", () => {
    setBrowserLanguage("fr-FR");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: en")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("prefers a stored locale over the browser language", () => {
    localStorage.setItem("rexab_locale", "ru");
    setBrowserLanguage("en-US");

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
  });

  it("persists a manual locale switch and re-renders with new translations", async () => {
    const user = userEvent.setup();

    render(
      <LocaleProvider>
        <TestConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("locale: en")).toBeInTheDocument();

    await user.click(screen.getByText("switch to ru"));

    expect(screen.getByText("locale: ru")).toBeInTheDocument();
    expect(screen.getByText("Отмена")).toBeInTheDocument();
    expect(localStorage.getItem("rexab_locale")).toBe("ru");
  });

  it("falls back to the key itself for a missing translation", () => {
    render(
      <LocaleProvider>
        <MissingKeyConsumer />
      </LocaleProvider>,
    );

    expect(screen.getByText("nonexistent.key")).toBeInTheDocument();
  });

  it("throws when used outside a LocaleProvider", () => {
    function Bare() {
      useTranslation();
      return null;
    }
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<Bare />)).toThrow(
      "useTranslation must be used within a LocaleProvider",
    );

    spy.mockRestore();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run lib/i18n/LocaleProvider.test.tsx`
Expected: FAIL — `Cannot find module '@/lib/i18n/LocaleProvider'`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/lib/i18n/LocaleProvider.tsx
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { en } from "@/lib/i18n/dictionaries/en";
import { ru } from "@/lib/i18n/dictionaries/ru";
import type { Locale, Vars } from "@/lib/i18n/types";

const STORAGE_KEY = "rexab_locale";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Vars) => string;
  tList: (key: string) => string[];
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function detectLocale(): Locale {
  if (
    typeof navigator !== "undefined" &&
    navigator.language.toLowerCase().startsWith("ru")
  ) {
    return "ru";
  }
  return "en";
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const resolved: Locale =
      stored === "en" || stored === "ru" ? stored : detectLocale();

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLocaleState(resolved);

    if (!stored) localStorage.setItem(STORAGE_KEY, resolved);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    localStorage.setItem(STORAGE_KEY, next);
    setLocaleState(next);
  }, []);

  const t = useCallback(
    (key: string, vars: Vars = {}) => {
      const dict = locale === "ru" ? ru : en;
      const entry = dict[key];

      if (entry === undefined) {
        if (process.env.NODE_ENV !== "production") {
          console.warn(`Missing translation for key "${key}"`);
        }
        return key;
      }

      if (typeof entry === "function") return entry(vars);

      if (Array.isArray(entry)) {
        if (process.env.NODE_ENV !== "production") {
          console.warn(`Key "${key}" is a list; use tList() instead of t()`);
        }
        return key;
      }

      return entry;
    },
    [locale],
  );

  const tList = useCallback(
    (key: string) => {
      const dict = locale === "ru" ? ru : en;
      const entry = dict[key];

      if (Array.isArray(entry)) return entry;

      if (process.env.NODE_ENV !== "production") {
        console.warn(`Missing or non-list translation for key "${key}"`);
      }
      return [];
    },
    [locale],
  );

  if (locale === null) return null;

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t, tList }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useTranslation(): LocaleContextValue {
  const context = useContext(LocaleContext);

  if (!context) {
    throw new Error("useTranslation must be used within a LocaleProvider");
  }

  return context;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run lib/i18n/LocaleProvider.test.tsx`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/i18n/LocaleProvider.tsx frontend/lib/i18n/LocaleProvider.test.tsx
git commit -m "feat(i18n): add LocaleProvider with browser detection and persistence"
```

---

## Task 4: `LanguageSwitcher` component

**Files:**
- Create: `frontend/components/LanguageSwitcher.tsx`
- Test: `frontend/components/LanguageSwitcher.test.tsx`

**Interfaces:**
- Consumes: `useTranslation` from Task 3; `Locale` from Task 2; `clsx` from `frontend/lib/clsx.ts` (existing).
- Produces: `LanguageSwitcher({ variant?: "light" | "dark" }): JSX.Element`. `variant` controls styling for the dark landing-page navbar vs. the light app shell — consumed by Task 5.

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/components/LanguageSwitcher.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { LocaleProvider } from "@/lib/i18n/LocaleProvider";

describe("LanguageSwitcher", () => {
  it("switches the active locale when a language button is clicked", async () => {
    const user = userEvent.setup();

    render(
      <LocaleProvider>
        <LanguageSwitcher />
      </LocaleProvider>,
    );

    const ruButton = screen.getByRole("button", { name: "RU" });
    const enButton = screen.getByRole("button", { name: "EN" });

    expect(enButton).toHaveAttribute("aria-pressed", "true");
    expect(ruButton).toHaveAttribute("aria-pressed", "false");

    await user.click(ruButton);

    expect(ruButton).toHaveAttribute("aria-pressed", "true");
    expect(enButton).toHaveAttribute("aria-pressed", "false");
    expect(localStorage.getItem("rexab_locale")).toBe("ru");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run components/LanguageSwitcher.test.tsx`
Expected: FAIL — `Cannot find module '@/components/LanguageSwitcher'`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/components/LanguageSwitcher.tsx
"use client";

import { useTranslation } from "@/lib/i18n/LocaleProvider";
import { clsx } from "@/lib/clsx";
import type { Locale } from "@/lib/i18n/types";

interface LanguageSwitcherProps {
  variant?: "light" | "dark";
}

const OPTIONS: { locale: Locale; label: string }[] = [
  { locale: "en", label: "EN" },
  { locale: "ru", label: "RU" },
];

export function LanguageSwitcher({ variant = "light" }: LanguageSwitcherProps) {
  const { locale, setLocale } = useTranslation();

  return (
    <div
      className={clsx(
        "flex items-center gap-0.5 rounded-lg border p-0.5 text-xs font-medium",
        variant === "dark" ? "border-white/15 bg-white/5" : "border-border bg-card",
      )}
    >
      {OPTIONS.map((option) => (
        <button
          key={option.locale}
          type="button"
          onClick={() => setLocale(option.locale)}
          aria-pressed={locale === option.locale}
          className={clsx(
            "rounded-md px-2 py-1 transition-colors",
            locale === option.locale
              ? "bg-accent text-white"
              : variant === "dark"
                ? "text-dark-muted hover:text-white"
                : "text-secondary hover:text-primary",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run components/LanguageSwitcher.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/LanguageSwitcher.tsx frontend/components/LanguageSwitcher.test.tsx
git commit -m "feat(i18n): add LanguageSwitcher toggle component"
```

---

## Task 5: Wire root layout, `AppShell`, and `Navbar`

**Files:**
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/components/AppShell.tsx`
- Modify: `frontend/components/landing/Navbar.tsx`

**Interfaces:**
- Consumes: `LocaleProvider` (Task 3), `useTranslation` (Task 3), `LanguageSwitcher` (Task 4), dictionary keys `nav.*`, `landing.nav.*`, `landing.cta.getStarted` (Task 2).

- [ ] **Step 1: Wrap the app in `LocaleProvider`**

In `frontend/app/layout.tsx`:

```diff
 import { AuthProvider } from "@/lib/auth-context";
 import { ToastProvider } from "@/components/ui/Toast";
+import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
```

```diff
       <body className="min-h-full bg-bg text-primary antialiased">
-        <AuthProvider>
-          <ToastProvider>{children}</ToastProvider>
-        </AuthProvider>
+        <LocaleProvider>
+          <AuthProvider>
+            <ToastProvider>{children}</ToastProvider>
+          </AuthProvider>
+        </LocaleProvider>
       </body>
```

- [ ] **Step 2: Wire `AppShell.tsx`**

Add the import and hook:

```diff
 import { useAuth } from "@/lib/auth-context";
 import { clsx } from "@/lib/clsx";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+import { LanguageSwitcher } from "@/components/LanguageSwitcher";
-
-const NAV_ITEMS = [
-  { href: "/dashboard", label: "Dashboard", icon: "🏠" },
-  { href: "/settings", label: "Settings", icon: "⚙️" },
-];
```

Move `NAV_ITEMS` inside the component (it now needs `t`) and add the hook call:

```diff
 export function AppShell({ children }: { children: ReactNode }) {
   const { user, isLoading, logout } = useAuth();
+  const { t } = useTranslation();
   const router = useRouter();
   const pathname = usePathname();
   const [menuOpen, setMenuOpen] = useState(false);
+
+  const navItems = [
+    { href: "/dashboard", label: t("nav.dashboard"), icon: "🏠" },
+    { href: "/settings", label: t("nav.settings"), icon: "⚙️" },
+  ];
```

Replace the two `NAV_ITEMS.map(...)` call sites (desktop `<nav>` and mobile bottom `<nav>`) with `navItems.map(...)`.

Add the switcher next to the header's profile menu (replacing the empty spacer span), so the header's flex row reads: brand on the left (mobile only), then `LanguageSwitcher` + profile menu button grouped on the right:

```diff
             <span className="hidden md:block" />
-            <div className="relative">
+            <div className="flex items-center gap-3">
+              <LanguageSwitcher />
+              <div className="relative">
```

This opens a new wrapping `<div className="relative">` around the existing profile-menu `<button>` and its dropdown `<div role="menu">`; close it with an extra `</div>` right after the existing closing `</div>` that currently ends the profile menu's `relative` wrapper (i.e. the wrapper nesting grows by one level, no JSX is deleted).

```diff
                     onClick={() => setMenuOpen(false)}
                     className="block px-4 py-2.5 text-sm text-primary hover:bg-bg"
                   >
-                    Settings
+                    {t("nav.settings")}
                   </Link>
                   <button
                     role="menuitem"
                     onClick={() => {
                       setMenuOpen(false);
                       logout();
                       router.replace("/login");
                     }}
                     className="block w-full px-4 py-2.5 text-left text-sm text-negative hover:bg-negative-bg"
                   >
-                    Log out
+                    {t("nav.logout")}
                   </button>
```

- [ ] **Step 3: Wire `Navbar.tsx`**

```diff
 import { clsx } from "@/lib/clsx";
 import { Container } from "@/components/ui/Container";
-
-const LINKS = [
-  { href: "#how-it-works", label: "How it works" },
-  { href: "#features", label: "Features" },
-  { href: "#use-cases", label: "Use cases" },
-];
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+import { LanguageSwitcher } from "@/components/LanguageSwitcher";

 export function Navbar() {
+  const { t } = useTranslation();
   const [isScrolled, setIsScrolled] = useState(false);
   const [isMenuOpen, setIsMenuOpen] = useState(false);
+
+  const links = [
+    { href: "#how-it-works", label: t("landing.nav.howItWorks") },
+    { href: "#features", label: t("landing.nav.features") },
+    { href: "#use-cases", label: t("landing.nav.useCases") },
+  ];
```

Replace both `LINKS.map(...)` call sites (desktop + mobile) with `links.map(...)`.

```diff
-          <Link
-            href="/login"
-            className={...}
-          >
-            Login
-          </Link>
+          <Link href="/login" className={...}>
+            {t("landing.nav.login")}
+          </Link>
+          <LanguageSwitcher variant={light ? "light" : "dark"} />
           <Link
             href="/register"
             className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-all hover:-translate-y-px hover:bg-accent-hover active:scale-[0.98]"
           >
-            Get started
+            {t("landing.cta.getStarted")}
           </Link>
```

```diff
           aria-label={isMenuOpen ? "Close menu" : "Open menu"}
+          aria-label={isMenuOpen ? t("landing.nav.closeMenu") : t("landing.nav.openMenu")}
```

(remove the old `aria-label` line, keep only the new one)

Mobile menu panel — same `Login`/`Get started` replacements:

```diff
             <Link href="/login" ...>
-              Login
+              {t("landing.nav.login")}
             </Link>
             <Link href="/register" ...>
-              Get started
+              {t("landing.cta.getStarted")}
             </Link>
```

- [ ] **Step 4: Run the full suite and lint**

Run: `npm test` and `npm run lint` (from `frontend/`)
Expected: all existing tests still PASS (nothing yet asserts on `AppShell`/`Navbar` text), lint clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/layout.tsx frontend/components/AppShell.tsx frontend/components/landing/Navbar.tsx
git commit -m "feat(i18n): wire LocaleProvider into app shell and navbar"
```

---

## Task 6: Wire login and register pages

**Files:**
- Modify: `frontend/app/login/page.tsx`
- Modify: `frontend/app/register/page.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `auth.login.*`, `auth.register.*` (Task 2).

- [ ] **Step 1: Wire `login/page.tsx`**

```diff
 import { useAuth } from "@/lib/auth-context";
 import { getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import { Button } from "@/components/ui/Button";
```

```diff
 export default function LoginPage() {
   const { login, user, isLoading: authLoading } = useAuth();
+  const { t } = useTranslation();
   const router = useRouter();
```

```diff
-        <h1 className="text-xl font-semibold text-primary">Welcome back</h1>
+        <h1 className="text-xl font-semibold text-primary">{t("auth.login.title")}</h1>
         <p className="mt-1 text-sm text-secondary">
-          Log in to see your rooms and balances.
+          {t("auth.login.subtitle")}
         </p>
```

```diff
           <Input
             id="email"
             type="email"
-            label="Email"
+            label={t("auth.login.emailLabel")}
             autoComplete="email"
```

```diff
           <Input
             id="password"
             type="password"
-            label="Password"
+            label={t("auth.login.passwordLabel")}
             autoComplete="current-password"
```

```diff
           <Button type="submit" isLoading={isSubmitting} className="mt-2">
-            Log in
+            {t("auth.login.submit")}
           </Button>
         </form>

         <p className="mt-6 text-center text-sm text-secondary">
-          No account?{" "}
+          {t("auth.login.noAccount")}{" "}
           <Link href="/register" className="font-medium text-accent">
-            Create one
+            {t("auth.login.createOne")}
           </Link>
         </p>
```

- [ ] **Step 2: Wire `register/page.tsx`**

```diff
 import { useAuth } from "@/lib/auth-context";
 import { getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import { Button } from "@/components/ui/Button";
```

```diff
 export default function RegisterPage() {
   const { register, user, isLoading: authLoading } = useAuth();
+  const { t } = useTranslation();
   const router = useRouter();
```

```diff
     if (password.length < 8) {
-      setError("Password must be at least 8 characters.");
+      setError(t("auth.register.passwordTooShort"));
       return;
     }
```

```diff
         <h1 className="text-xl font-semibold text-primary">
-          Create your account
+          {t("auth.register.title")}
         </h1>
         <p className="mt-1 text-sm text-secondary">
-          Split bills with friends and roommates.
+          {t("auth.register.subtitle")}
         </p>
```

```diff
           <Input
             id="firstName"
-            label="Name"
+            label={t("auth.register.nameLabel")}
             autoComplete="given-name"
```

```diff
           <Input
             id="email"
             type="email"
-            label="Email"
+            label={t("auth.register.emailLabel")}
             autoComplete="email"
```

```diff
           <Input
             id="password"
             type="password"
-            label="Password"
+            label={t("auth.register.passwordLabel")}
             autoComplete="new-password"
```

```diff
           <Button type="submit" isLoading={isSubmitting} className="mt-2">
-            Create account
+            {t("auth.register.submit")}
           </Button>
         </form>

         <p className="mt-6 text-center text-sm text-secondary">
-          Already have an account?{" "}
+          {t("auth.register.haveAccount")}{" "}
           <Link href="/login" className="font-medium text-accent">
-            Log in
+            {t("auth.register.logIn")}
           </Link>
         </p>
```

- [ ] **Step 3: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/login/page.tsx frontend/app/register/page.tsx
git commit -m "feat(i18n): translate login and register pages"
```

---

## Task 7: Wire dashboard page + `RoomCard`

**Files:**
- Modify: `frontend/app/(app)/dashboard/page.tsx`
- Modify: `frontend/components/RoomCard.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `stats.*`, `dashboard.*`, `room.actions.create`, `room.actions.join`, `room.card.*` (Task 2).

- [ ] **Step 1: Wire `dashboard/page.tsx`**

```diff
 import { useAuth } from "@/lib/auth-context";
 import { api, getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export default function DashboardPage() {
   const { user } = useAuth();
+  const { t } = useTranslation();
   const [rooms, setRooms] = useState<RoomWithBalance[] | null>(null);
```

```diff
         <h1 className="text-2xl font-semibold text-primary">
-          Good to see you, {user?.first_name}
+          {t("dashboard.greeting", { name: user?.first_name ?? "" })}
         </h1>
         <p className="mt-1 text-sm text-secondary">
-          Here&apos;s what&apos;s happening in your rooms.
+          {t("dashboard.subtitle")}
         </p>
```

```diff
           <StatTile
-            label="You owe"
+            label={t("stats.youOwe")}
             value={formatSignedMoney(-youOwe)}
             tone={youOwe > 0 ? "negative" : "neutral"}
           />
           <StatTile
-            label="Owed to you"
+            label={t("stats.owedToYou")}
             value={formatSignedMoney(youAreOwed)}
             tone={youAreOwed > 0 ? "positive" : "neutral"}
           />
           <StatTile
-            label="Balance"
+            label={t("stats.balance")}
             value={formatSignedMoney(netBalance)}
```

```diff
-          <h2 className="text-lg font-semibold text-primary">Your rooms</h2>
+          <h2 className="text-lg font-semibold text-primary">{t("dashboard.yourRooms")}</h2>
           <div className="flex gap-2">
             <Button
               variant="secondary"
               size="sm"
               onClick={() => setIsJoinOpen(true)}
             >
-              Join room
+              {t("room.actions.join")}
             </Button>
             <Button size="sm" onClick={() => setIsCreateOpen(true)}>
-              + Create room
+              + {t("room.actions.create")}
             </Button>
           </div>
```

```diff
           <EmptyState
             icon="🏠"
-            title="No rooms yet"
-            description="Create a room to start splitting expenses, or join one with an invite code."
+            title={t("dashboard.noRoomsTitle")}
+            description={t("dashboard.noRoomsDescription")}
             action={
               <Button size="sm" onClick={() => setIsCreateOpen(true)}>
-                + Create room
+                + {t("room.actions.create")}
               </Button>
             }
           />
```

- [ ] **Step 2: Wire `RoomCard.tsx`**

```diff
 import Link from "next/link";
 import { formatSignedMoney } from "@/lib/format";
 import { clsx } from "@/lib/clsx";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Room } from "@/types/api";
+
+("use client");
```

(Add `"use client";` as the actual first line of the file, above the imports — this file has no directive today and now calls a hook.)

```diff
 export function RoomCard({ room, balance }: RoomCardProps) {
+  const { t } = useTranslation();
   const tone =
```

```diff
         <p className="font-medium text-primary">
-          {room.name ?? `Room ${room.code}`}
+          {room.name ?? t("room.card.unnamedRoom", { code: room.code })}
         </p>
         <p className="text-sm text-secondary">
-          {room.members_count}{" "}
-          {room.members_count === 1 ? "member" : "members"}
+          {t("room.card.memberCount", { count: room.members_count })}
         </p>
```

- [ ] **Step 3: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 4: Commit**

```bash
git add "frontend/app/(app)/dashboard/page.tsx" frontend/components/RoomCard.tsx
git commit -m "feat(i18n): translate dashboard page and room card"
```

---

## Task 8: Wire `CreateRoomDialog` + `JoinRoomDialog`

**Files:**
- Modify: `frontend/components/CreateRoomDialog.tsx`
- Modify: `frontend/components/JoinRoomDialog.tsx`
- Modify: `frontend/components/CreateRoomDialog.test.tsx` (existing test breaks once `t()` requires a provider)

**Interfaces:**
- Consumes: `useTranslation` (Task 3), `LocaleProvider` (Task 3), keys `room.actions.create`, `room.actions.join`, `common.cancel`, `dialog.createRoom.*`, `dialog.joinRoom.*` (Task 2).

- [ ] **Step 1: Wire `CreateRoomDialog.tsx`**

```diff
 import { api, getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Room } from "@/types/api";
```

```diff
 export function CreateRoomDialog({
   isOpen,
   onClose,
   onCreated,
 }: CreateRoomDialogProps) {
+  const { t } = useTranslation();
   const [name, setName] = useState("");
```

```diff
-    <Modal isOpen={isOpen} onClose={onClose} title="Create room">
+    <Modal isOpen={isOpen} onClose={onClose} title={t("room.actions.create")}>
       <form onSubmit={handleSubmit} className="flex flex-col gap-4">
         <Input
           id="room-name"
-          label="Room name"
-          placeholder="Apartment"
+          label={t("dialog.createRoom.nameLabel")}
+          placeholder={t("dialog.createRoom.namePlaceholder")}
```

```diff
           <Button type="button" variant="secondary" onClick={onClose}>
-            Cancel
+            {t("common.cancel")}
           </Button>
           <Button type="submit" isLoading={isSubmitting}>
-            Create room
+            {t("room.actions.create")}
           </Button>
```

- [ ] **Step 2: Wire `JoinRoomDialog.tsx`**

```diff
 import { api, getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Room } from "@/types/api";
```

```diff
 export function JoinRoomDialog({
   isOpen,
   onClose,
   onJoined,
 }: JoinRoomDialogProps) {
+  const { t } = useTranslation();
   const [code, setCode] = useState("");
```

```diff
-    <Modal isOpen={isOpen} onClose={onClose} title="Join a room">
+    <Modal isOpen={isOpen} onClose={onClose} title={t("dialog.joinRoom.title")}>
       <form onSubmit={handleSubmit} className="flex flex-col gap-4">
         <Input
           id="invite-code"
-          label="Invitation code"
+          label={t("dialog.joinRoom.codeLabel")}
           placeholder="X7K4-P9Q2"
```

```diff
           <Button type="button" variant="secondary" onClick={onClose}>
-            Cancel
+            {t("common.cancel")}
           </Button>
           <Button type="submit" isLoading={isSubmitting}>
-            Join room
+            {t("room.actions.join")}
           </Button>
```

- [ ] **Step 3: Update `CreateRoomDialog.test.tsx` to wrap in `LocaleProvider`**

```diff
 import { render, screen, waitFor } from "@testing-library/react";
 import userEvent from "@testing-library/user-event";
 import { describe, expect, it, vi } from "vitest";
 import { CreateRoomDialog } from "@/components/CreateRoomDialog";
+import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
 import { api, ApiError } from "@/lib/api";
```

Wrap all three `render(<CreateRoomDialog .../>)` calls:

```diff
-    render(
-      <CreateRoomDialog isOpen onClose={onClose} onCreated={onCreated} />,
-    );
+    render(
+      <LocaleProvider>
+        <CreateRoomDialog isOpen onClose={onClose} onCreated={onCreated} />
+      </LocaleProvider>,
+    );
```

(apply the same wrapping to the second and third `render(...)` calls in that file — the assertions themselves, e.g. `screen.getByLabelText("Room name")` and `screen.getByRole("button", { name: "Create room" })`, stay unchanged since the default test locale resolves to English.)

- [ ] **Step 4: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS (including the updated `CreateRoomDialog.test.tsx`), clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/CreateRoomDialog.tsx frontend/components/JoinRoomDialog.tsx frontend/components/CreateRoomDialog.test.tsx
git commit -m "feat(i18n): translate create/join room dialogs"
```

---

## Task 9: Wire `rooms/[id]/page.tsx`

**Files:**
- Modify: `frontend/app/(app)/rooms/[id]/page.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `stats.*`, `room.actions.addPayment`, `room.actions.remove`, `room.card.memberCount`, `room.page.*`, `common.confirm` (Task 2).

- [ ] **Step 1: Add the hook**

```diff
 import { useAuth } from "@/lib/auth-context";
 import { useRoomData } from "@/hooks/useRoomData";
 import { api, getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import { useToast } from "@/components/ui/Toast";
```

```diff
 export default function RoomPage() {
   const params = useParams<{ id: string }>();
   const roomId = Number(params.id);
   const router = useRouter();
   const { user } = useAuth();
+  const { t } = useTranslation();
   const { showToast } = useToast();
```

- [ ] **Step 2: Header, member count, delete/leave button**

```diff
         <p className="mt-1 text-sm text-secondary">
-          {members.length} {members.length === 1 ? "member" : "members"} ·
-          code <span className="font-mono">{room.code}</span>
+          {t("room.card.memberCount", { count: members.length })} ·{" "}
+          code <span className="font-mono">{room.code}</span>
         </p>
```

```diff
         <Button variant="ghost" size="sm" onClick={() => setLeaveOrDelete(true)}>
-          {room.is_owner ? "Delete room" : "Leave room"}
+          {room.is_owner ? t("room.page.deleteRoom") : t("room.page.leaveRoom")}
         </Button>
```

- [ ] **Step 3: Stat tiles**

```diff
         <StatTile
-          label="You owe"
+          label={t("stats.youOwe")}
           value={formatSignedMoney(-dashboard.you_owe)}
           tone={dashboard.you_owe > 0 ? "negative" : "neutral"}
         />
         <StatTile
-          label="Owed to you"
+          label={t("stats.owedToYou")}
           value={formatSignedMoney(dashboard.you_are_owed)}
           tone={dashboard.you_are_owed > 0 ? "positive" : "neutral"}
         />
         <StatTile
-          label="Balance"
+          label={t("stats.balance")}
           value={formatSignedMoney(dashboard.balance)}
```

- [ ] **Step 4: Add-payment button**

```diff
               <Button size="sm" onClick={() => setIsAddPaymentOpen(true)}>
-                + Add payment
+                + {t("room.actions.addPayment")}
               </Button>
```

- [ ] **Step 5: Confirm dialogs**

```diff
         onConfirm={handleSettle}
-        title="Request settlement?"
+        title={t("room.page.requestSettlementTitle")}
         description={
           settleTarget
-            ? `Mark ${formatMoney(settleTarget.amount)} as being settled between these two members. The receiver will need to confirm.`
+            ? t("room.page.requestSettlementDescription", {
+                amount: formatMoney(settleTarget.amount),
+              })
             : ""
         }
-        confirmLabel="Request settlement"
+        confirmLabel={t("room.page.requestSettlementConfirm")}
```

```diff
         onConfirm={handleConfirmSettlement}
-        title="Confirm payment?"
-        description="Did you actually receive this payment? Confirming will mark the debt as settled."
-        confirmLabel="Confirm"
+        title={t("room.page.confirmPaymentTitle")}
+        description={t("room.page.confirmPaymentDescription")}
+        confirmLabel={t("common.confirm")}
```

```diff
         onConfirm={handleRemoveMember}
-        title="Remove member?"
+        title={t("room.page.removeMemberTitle")}
         description={
           removeTarget
-            ? `${removeTarget.first_name} will lose access to this room.`
+            ? t("room.page.removeMemberDescription", { name: removeTarget.first_name })
             : ""
         }
-        confirmLabel="Remove"
+        confirmLabel={t("room.actions.remove")}
```

```diff
         onConfirm={handleLeaveOrDelete}
-        title={room.is_owner ? "Delete this room?" : "Leave this room?"}
+        title={room.is_owner ? t("room.page.deleteConfirmTitle") : t("room.page.leaveConfirmTitle")}
         description={
           room.is_owner
-            ? "This permanently deletes the room and all its payments, receipts and settlements. This cannot be undone."
-            : "You can rejoin later with the invite code."
+            ? t("room.page.deleteConfirmDescription")
+            : t("room.page.leaveConfirmDescription")
         }
-        confirmLabel={room.is_owner ? "Delete room" : "Leave room"}
+        confirmLabel={room.is_owner ? t("room.page.deleteRoom") : t("room.page.leaveRoom")}
```

- [ ] **Step 6: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 7: Commit**

```bash
git add "frontend/app/(app)/rooms/[id]/page.tsx"
git commit -m "feat(i18n): translate room detail page"
```

---

## Task 10: Wire `PaymentList` + `AddPaymentDialog`

**Files:**
- Modify: `frontend/components/PaymentList.tsx`
- Modify: `frontend/components/AddPaymentDialog.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `payment.list.*`, `common.paidWord`, `room.actions.addPayment`, `common.cancel`, `dialog.addPayment.*` (Task 2).

- [ ] **Step 1: Wire `PaymentList.tsx`**

```diff
 import { Card } from "@/components/ui/Card";
 import { EmptyState } from "@/components/ui/EmptyState";
 import { formatDateTime, formatMoney } from "@/lib/format";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Payment } from "@/types/api";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function PaymentList({ payments }: PaymentListProps) {
+  const { t } = useTranslation();
+
   return (
     <Card>
       <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
-        Payments
+        {t("payment.list.title")}
       </h2>

       {payments.length === 0 ? (
         <EmptyState
           icon="🧾"
-          title="No payments yet"
-          description="Add the first expense for this room."
+          title={t("payment.list.emptyTitle")}
+          description={t("payment.list.emptyDescription")}
         />
```

```diff
                   <p className="font-medium text-primary">
-                    {payment.description || "Expense"}
+                    {payment.description || t("payment.list.fallbackDescription")}
                   </p>
                   <p className="text-sm text-secondary">
-                    {payment.payer_name} paid ·{" "}
+                    {payment.payer_name} {t("common.paidWord")} ·{" "}
                     {formatDateTime(payment.created_at)}
                   </p>
```

- [ ] **Step 2: Wire `AddPaymentDialog.tsx`**

```diff
 import { api, getErrorMessage } from "@/lib/api";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Member } from "@/types/api";
```

```diff
 export function AddPaymentDialog({
   isOpen,
   onClose,
   roomId,
   members,
   currentUserId,
   onAdded,
 }: AddPaymentDialogProps) {
+  const { t } = useTranslation();
   const [amount, setAmount] = useState("");
```

```diff
     if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
-      setError("Enter a valid amount.");
+      setError(t("dialog.addPayment.invalidAmount"));
       return;
     }
```

```diff
-    <Modal isOpen={isOpen} onClose={onClose} title="Add payment">
+    <Modal isOpen={isOpen} onClose={onClose} title={t("room.actions.addPayment")}>
       <form onSubmit={handleSubmit} className="flex flex-col gap-4">
         <Input
           id="amount"
-          label="Amount"
+          label={t("dialog.addPayment.amountLabel")}
           inputMode="decimal"
-          placeholder="100"
+          placeholder={t("dialog.addPayment.amountPlaceholder")}
```

```diff
         <Input
           id="description"
-          label="Description"
-          placeholder="Dinner"
+          label={t("dialog.addPayment.descriptionLabel")}
+          placeholder={t("dialog.addPayment.descriptionPlaceholder")}
```

```diff
           <label htmlFor="payer" className="text-sm font-medium text-primary">
-            Paid by
+            {t("dialog.addPayment.paidByLabel")}
           </label>
```

```diff
               <option key={member.user_id} value={member.user_id}>
                 {member.first_name}
-                {member.user_id === currentUserId ? " (you)" : ""}
+                {member.user_id === currentUserId ? t("dialog.addPayment.youSuffix") : ""}
               </option>
```

```diff
           <Button type="button" variant="secondary" onClick={onClose}>
-            Cancel
+            {t("common.cancel")}
           </Button>
           <Button type="submit" isLoading={isSubmitting}>
-            Add payment
+            {t("room.actions.addPayment")}
           </Button>
```

- [ ] **Step 3: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/PaymentList.tsx frontend/components/AddPaymentDialog.tsx
git commit -m "feat(i18n): translate payment list and add-payment dialog"
```

---

## Task 11: Wire `MemberList` + `InviteDialog`

**Files:**
- Modify: `frontend/components/MemberList.tsx`
- Modify: `frontend/components/InviteDialog.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `member.list.*`, `room.actions.remove`, `room.actions.addMember`, `dialog.invite.*`, `room.actions.copyCode`, `room.actions.copied` (Task 2).

- [ ] **Step 1: Wire `MemberList.tsx`**

```diff
 import { Card } from "@/components/ui/Card";
 import { Button } from "@/components/ui/Button";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Member } from "@/types/api";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function MemberList({
   members,
   isOwner,
   onInvite,
   onRemove,
 }: MemberListProps) {
+  const { t } = useTranslation();
+
   return (
     <Card>
       <div className="mb-3 flex items-center justify-between">
         <h2 className="text-sm font-semibold uppercase tracking-wide text-secondary">
-          Members
+          {t("member.list.title")}
         </h2>
```

```diff
             <span className="flex-1 text-primary">{member.first_name}</span>
-            {member.is_owner && <span aria-label="Owner">👑</span>}
+            {member.is_owner && <span aria-label={t("member.list.ownerLabel")}>👑</span>}
             {isOwner && !member.is_owner && (
               <button
                 onClick={() => onRemove(member)}
                 className="text-xs font-medium text-negative hover:underline"
               >
-                Remove
+                {t("room.actions.remove")}
               </button>
             )}
```

```diff
       <Button variant="secondary" size="sm" className="mt-3 w-full" onClick={onInvite}>
-        + Add member
+        + {t("room.actions.addMember")}
       </Button>
```

- [ ] **Step 2: Wire `InviteDialog.tsx`**

```diff
 import { Modal } from "@/components/ui/Modal";
 import { Button } from "@/components/ui/Button";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function InviteDialog({ isOpen, onClose, code }: InviteDialogProps) {
+  const { t } = useTranslation();
   const [copied, setCopied] = useState(false);
```

```diff
-    <Modal isOpen={isOpen} onClose={onClose} title="Invite to room">
+    <Modal isOpen={isOpen} onClose={onClose} title={t("dialog.invite.title")}>
       <p className="text-sm text-secondary">
-        Share this code with friends so they can join.
+        {t("dialog.invite.description")}
       </p>
```

```diff
         <Button onClick={handleCopy}>
-          {copied ? "Copied!" : "Copy code"}
+          {copied ? t("room.actions.copied") : t("room.actions.copyCode")}
         </Button>
```

- [ ] **Step 3: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/MemberList.tsx frontend/components/InviteDialog.tsx
git commit -m "feat(i18n): translate member list and invite dialog"
```

---

## Task 12: Wire `SettlementList` + `WhoOwesWhom`

**Files:**
- Modify: `frontend/components/SettlementList.tsx`
- Modify: `frontend/components/WhoOwesWhom.tsx`
- Modify: `frontend/components/WhoOwesWhom.test.tsx` (existing test breaks once `t()` requires a provider)

**Interfaces:**
- Consumes: `useTranslation`/`LocaleProvider` (Task 3), keys `settlement.list.*`, `room.actions.confirmPayment`, `common.paidWord`, `whoOwesWhom.*`, `room.actions.settleUp` (Task 2).

- [ ] **Step 1: Wire `SettlementList.tsx`**

```diff
 import { Card } from "@/components/ui/Card";
 import { Button } from "@/components/ui/Button";
 import { EmptyState } from "@/components/ui/EmptyState";
 import { formatDate, formatMoney } from "@/lib/format";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Member, Settlement } from "@/types/api";
```

```diff
 export function SettlementList({
   settlements,
   members,
   currentUserId,
   onConfirm,
   isConfirming,
 }: SettlementListProps) {
+  const { t } = useTranslation();
   const pending = settlements.filter((s) => s.status === "pending");
```

```diff
       <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
-        Settlements
+        {t("settlement.list.title")}
       </h2>

       {pending.length === 0 && history.length === 0 ? (
-        <EmptyState icon="💸" title="No settlements yet" />
+        <EmptyState icon="💸" title={t("settlement.list.emptyTitle")} />
```

```diff
                       <span className="font-medium">
                         {nameFor(members, settlement.from_user_id)}
                       </span>{" "}
-                      owes{" "}
+                      {t("settlement.list.owesWord")}{" "}
                       <span className="font-medium">
                         {nameFor(members, settlement.to_user_id)}
                       </span>
```

```diff
                         isLoading={isConfirming === settlement.id}
                       >
-                        Confirm payment
+                        {t("room.actions.confirmPayment")}
                       </Button>
                     ) : (
                       <p className="mt-2 text-xs text-warning">
-                        Waiting for confirmation
+                        {t("settlement.list.waitingConfirmation")}
                       </p>
```

```diff
                   {nameFor(members, settlement.from_user_id)}
                   </span>{" "}
-                  paid{" "}
+                  {t("common.paidWord")}{" "}
                   <span className="font-medium text-primary">
```

- [ ] **Step 2: Wire `WhoOwesWhom.tsx`**

```diff
 import { Card } from "@/components/ui/Card";
 import { Button } from "@/components/ui/Button";
 import { EmptyState } from "@/components/ui/EmptyState";
 import { formatMoney } from "@/lib/format";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import type { Member, Transfer } from "@/types/api";
```

```diff
 export function WhoOwesWhom({
   transfers,
   members,
   currentUserId,
   onSettle,
 }: WhoOwesWhomProps) {
+  const { t } = useTranslation();
+
   return (
     <Card>
       <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-secondary">
-        Who owes whom
+        {t("whoOwesWhom.title")}
       </h2>

       {transfers.length === 0 ? (
-        <EmptyState icon="🎉" title="Everyone is settled up." />
+        <EmptyState icon="🎉" title={t("whoOwesWhom.emptyTitle")} />
```

```diff
                 {involvesCurrentUser && (
                   <Button size="sm" onClick={() => onSettle(transfer)}>
-                    Settle up
+                    {t("room.actions.settleUp")}
                   </Button>
                 )}
```

- [ ] **Step 3: Update `WhoOwesWhom.test.tsx` to wrap in `LocaleProvider`**

```diff
 import { render, screen } from "@testing-library/react";
 import userEvent from "@testing-library/user-event";
 import { describe, expect, it, vi } from "vitest";
 import { WhoOwesWhom } from "@/components/WhoOwesWhom";
+import { LocaleProvider } from "@/lib/i18n/LocaleProvider";
 import type { Member, Transfer } from "@/types/api";
```

Wrap all four `render(<WhoOwesWhom .../>)` calls in that file with `<LocaleProvider>...</LocaleProvider>`, e.g.:

```diff
-    render(
-      <WhoOwesWhom
-        transfers={[]}
-        members={members}
-        currentUserId={1}
-        onSettle={vi.fn()}
-      />,
-    );
+    render(
+      <LocaleProvider>
+        <WhoOwesWhom
+          transfers={[]}
+          members={members}
+          currentUserId={1}
+          onSettle={vi.fn()}
+        />
+      </LocaleProvider>,
+    );
```

(apply the same wrapping to the other three `render(...)` calls; assertions like `screen.getByText(/settled up/i)` and `screen.getByText("Settle up")` are unchanged since the default test locale is English.)

- [ ] **Step 4: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS (including updated `WhoOwesWhom.test.tsx`), clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/SettlementList.tsx frontend/components/WhoOwesWhom.tsx frontend/components/WhoOwesWhom.test.tsx
git commit -m "feat(i18n): translate settlement list and who-owes-whom"
```

---

## Task 13: Wire settings page, `Modal`, `ConfirmDialog`

**Files:**
- Modify: `frontend/app/(app)/settings/page.tsx`
- Modify: `frontend/components/ui/Modal.tsx`
- Modify: `frontend/components/ui/ConfirmDialog.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `nav.settings`, `nav.logout`, `settings.*`, `common.close`, `common.cancel`, `common.confirm` (Task 2).

- [ ] **Step 1: Wire `settings/page.tsx`**

```diff
 import { useAuth } from "@/lib/auth-context";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import { Card } from "@/components/ui/Card";
```

```diff
 export default function SettingsPage() {
   const { user, logout } = useAuth();
+  const { t } = useTranslation();
   const router = useRouter();
```

```diff
-      <h1 className="text-2xl font-semibold text-primary">Settings</h1>
+      <h1 className="text-2xl font-semibold text-primary">{t("nav.settings")}</h1>
```

```diff
             <p className="text-sm text-secondary">
-              {user.email ?? "No email on this account"}
+              {user.email ?? t("settings.noEmail")}
             </p>
```

```diff
         {user.telegram_id && (
           <p className="text-sm text-secondary">
-            Linked to Telegram (id {user.telegram_id})
+            {t("settings.linkedTelegram", { id: user.telegram_id })}
           </p>
         )}
```

```diff
       <Button variant="secondary" onClick={() => { logout(); router.replace("/login"); }}>
-        Log out
+        {t("nav.logout")}
       </Button>
```

- [ ] **Step 2: Wire `ui/Modal.tsx` close button**

```diff
 import { useEffect } from "react";
 import type { ReactNode } from "react";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function Modal({ isOpen, onClose, title, children }: ModalProps) {
+  const { t } = useTranslation();
+
   useEffect(() => {
```

```diff
           <button
             onClick={onClose}
-            aria-label="Закрыть"
+            aria-label={t("common.close")}
             className="rounded-md p-1 text-secondary hover:bg-bg hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
```

(This also fixes a pre-existing bug: the close button's `aria-label` was hardcoded to Russian regardless of any locale — it now correctly follows the selected language.)

- [ ] **Step 3: Wire `ui/ConfirmDialog.tsx` default labels**

```diff
 import { Modal } from "@/components/ui/Modal";
 import { Button } from "@/components/ui/Button";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function ConfirmDialog({
   isOpen,
   onClose,
   onConfirm,
   title,
   description,
-  confirmLabel = "Confirm",
+  confirmLabel,
   variant = "primary",
   isLoading = false,
   error,
 }: ConfirmDialogProps) {
+  const { t } = useTranslation();
+
   return (
```

```diff
         <Button variant="secondary" onClick={onClose}>
-          Cancel
+          {t("common.cancel")}
         </Button>
         <Button variant={variant} onClick={onConfirm} isLoading={isLoading}>
-          {confirmLabel}
+          {confirmLabel ?? t("common.confirm")}
         </Button>
```

(`confirmLabel` becomes optional with the translated default computed inline, since a prop default can't call a hook.)

- [ ] **Step 4: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add "frontend/app/(app)/settings/page.tsx" frontend/components/ui/Modal.tsx frontend/components/ui/ConfirmDialog.tsx
git commit -m "feat(i18n): translate settings page, modal close button, confirm dialog"
```

---

## Task 14: Wire `Hero` + `FinalCTA`

**Files:**
- Modify: `frontend/components/landing/Hero.tsx`
- Modify: `frontend/components/landing/FinalCTA.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `landing.hero.*`, `landing.cta.getStarted`, `landing.finalCta.*` (Task 2).

- [ ] **Step 1: Wire `Hero.tsx`**

```diff
 import { Container } from "@/components/ui/Container";
 import { Badge } from "@/components/ui/Badge";
 import { HeroDashboard } from "@/components/landing/HeroDashboard";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function Hero() {
+  const { t } = useTranslation();
+
   return (
```

```diff
             <Badge tone="dark">
               <Sparkle className="h-3 w-3 text-accent" aria-hidden="true" />
-              Shared expenses, simplified
+              {t("landing.hero.badge")}
             </Badge>
```

```diff
           >
-            Manage shared expenses
+            {t("landing.hero.headline")}
             <br />
-            without the{" "}
-            <span className="text-accent">headache.</span>
+            {t("landing.hero.headlineSuffix")}{" "}
+            <span className="text-accent">{t("landing.hero.headlineAccent")}</span>
           </motion.h1>
```

```diff
           >
-            Rexab makes it simple to track expenses, split costs and
-            settle debts with your roommates, friends and travel groups.
+            {t("landing.hero.subtitle")}
           </motion.p>
```

```diff
             <Link href="/register" className={...}>
-              Get started
+              {t("landing.cta.getStarted")}
               <ArrowRight className="h-4 w-4" aria-hidden="true" />
             </Link>
             <a href="#how-it-works" className={...}>
-              See how it works
+              {t("landing.hero.seeHowItWorks")}
             </a>
```

- [ ] **Step 2: Wire `FinalCTA.tsx`**

```diff
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function FinalCTA() {
+  const { t } = useTranslation();
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
-            Ready to stop doing the math?
+            {t("landing.finalCta.title")}
           </h2>
           <p className="mx-auto mt-4 max-w-md text-lg text-dark-muted">
-            Create your first room and keep shared expenses under
-            control.
+            {t("landing.finalCta.subtitle")}
           </p>
           <Link href="/register" className={...}>
-            Get started
+            {t("landing.cta.getStarted")}
             <ArrowRight className="h-4 w-4" aria-hidden="true" />
           </Link>
```

- [ ] **Step 3: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/landing/Hero.tsx frontend/components/landing/FinalCTA.tsx
git commit -m "feat(i18n): translate landing hero and final CTA"
```

---

## Task 15: Wire `mock-data.ts` + `HeroDashboard` + `InteractiveDemo`

**Files:**
- Modify: `frontend/components/landing/mock-data.ts`
- Modify: `frontend/components/landing/HeroDashboard.tsx`
- Modify: `frontend/components/landing/InteractiveDemo.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `landing.demo.*`, `landing.heroDashboard.*`, `room.actions.addPayment`, `stats.*`, `whoOwesWhom.title`, `member.list.title`, `settlement.list.title`, `landing.demo.tabs.expenses` (Task 2).
- Produces: `demoPayments` entries now shaped `{ labelKey: string; emoji: string; amount: number }` (renamed from `label`) — this is a structural change consumed by both files in this task, so both must be updated together.

- [ ] **Step 1: Rename `demoPayments.label` to `labelKey` in `mock-data.ts`**

```diff
 export const demoPayments = [
-  { label: "Dinner", emoji: "🍕", amount: 80 },
-  { label: "Groceries", emoji: "🛒", amount: 120 },
-  { label: "Internet", emoji: "📶", amount: 40 },
-  { label: "Utilities", emoji: "💡", amount: 180 },
+  { labelKey: "landing.demo.payments.dinner", emoji: "🍕", amount: 80 },
+  { labelKey: "landing.demo.payments.groceries", emoji: "🛒", amount: 120 },
+  { labelKey: "landing.demo.payments.internet", emoji: "📶", amount: 40 },
+  { labelKey: "landing.demo.payments.utilities", emoji: "💡", amount: 180 },
 ];
```

- [ ] **Step 2: Wire `HeroDashboard.tsx`**

```diff
 import { AnimatedNumber } from "@/components/landing/AnimatedNumber";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import {
   demoBalance,
   demoPayments,
-  demoRoomName,
   demoTransfers,
 } from "@/components/landing/mock-data";
```

```diff
 export function HeroDashboard() {
+  const { t } = useTranslation();
   const dinner = demoPayments[0];
```

```diff
         <div className="flex items-center justify-between">
-          <p className="font-semibold text-primary">{demoRoomName}</p>
+          <p className="font-semibold text-primary">{t("landing.demo.roomName")}</p>
```

```diff
         <p className="mt-5 text-xs font-medium uppercase tracking-wide text-secondary">
-          Your balance
+          {t("landing.heroDashboard.yourBalance")}
         </p>
```

```diff
           <div className="flex items-center justify-between">
-            <span className="text-secondary">You owe</span>
+            <span className="text-secondary">{t("stats.youOwe")}</span>
             <span className="font-medium text-primary">
               {demoBalance.youOwe} zł
             </span>
           </div>
           <div className="flex items-center justify-between">
-            <span className="text-secondary">Owed to you</span>
+            <span className="text-secondary">{t("stats.owedToYou")}</span>
             <span className="font-medium text-primary">
               {demoBalance.youAreOwed} zł
             </span>
           </div>
```

```diff
         <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
-          Who owes whom
+          {t("whoOwesWhom.title")}
         </p>
         <div className="mt-3 flex flex-col gap-2.5">
           {demoTransfers.map((transfer) => (
             <div key={`${transfer.from}-${transfer.to}`} ...>
               <span className="text-primary">
-                {transfer.from}{" "}
+                {transfer.from === "You" ? t("landing.demo.you") : transfer.from}{" "}
                 <span className="text-secondary">→</span>{" "}
-                {transfer.to}
+                {transfer.to === "You" ? t("landing.demo.you") : transfer.to}
               </span>
```

```diff
         <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
-          Recent payment
+          {t("landing.heroDashboard.recentPayment")}
         </p>
         <div className="mt-2 flex items-center justify-between text-sm">
           <span className="text-primary">
-            {dinner.emoji} {dinner.label}
+            {dinner.emoji} {t(dinner.labelKey)}
           </span>
```

```diff
         <button className={...}>
           <Plus className="h-4 w-4" aria-hidden="true" />
-          Add payment
+          {t("room.actions.addPayment")}
         </button>
       </motion.div>
```

```diff
         <p className="text-[11px] font-medium uppercase tracking-wide text-secondary">
-          You are owed
+          {t("landing.heroDashboard.youAreOwed")}
         </p>
```

```diff
       <FloatingCard className="-right-8 top-1/3 rotate-2" delay={1.3} duration={8}>
-        <p className="text-sm font-medium text-primary">✓ Settlement confirmed</p>
+        <p className="text-sm font-medium text-primary">
+          {t("landing.heroDashboard.settlementConfirmed")}
+        </p>
       </FloatingCard>
```

```diff
       <FloatingCard className="-left-6 bottom-2 rotate-1" delay={1.5} duration={6.5}>
         <p className="text-sm text-primary">
-          <span className="font-medium">Alex</span> paid
+          <span className="font-medium">Alex</span> {t("common.paidWord")}
         </p>
```

- [ ] **Step 3: Wire `InteractiveDemo.tsx`**

```diff
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
 import { clsx } from "@/lib/clsx";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import {
   demoBalance,
   demoMembers,
   demoPayments,
   demoSettlements,
 } from "@/components/landing/mock-data";
```

Each tab sub-component (`BalanceTab`, `ExpensesTab`, `MembersTab`, `SettlementsTab`) needs `t` — call `useTranslation()` inside each one directly (they're independent function components in the same file):

```diff
 function BalanceTab() {
+  const { t } = useTranslation();
   return (
     <div className="flex flex-col items-center gap-6 py-6 text-center">
       <div>
         <p className="text-xs font-medium uppercase tracking-wide text-secondary">
-          Balance
+          {t("stats.balance")}
         </p>
         <p className="mt-1 text-4xl font-semibold text-positive">
           +{demoBalance.balance} zł
         </p>
       </div>
       <div className="flex gap-10">
         <div>
-          <p className="text-xs text-secondary">You owe</p>
+          <p className="text-xs text-secondary">{t("stats.youOwe")}</p>
           <p className="mt-1 font-semibold text-primary">
             {demoBalance.youOwe} zł
           </p>
         </div>
         <div>
-          <p className="text-xs text-secondary">Owed to you</p>
+          <p className="text-xs text-secondary">{t("stats.owedToYou")}</p>
           <p className="mt-1 font-semibold text-primary">
             {demoBalance.youAreOwed} zł
           </p>
         </div>
       </div>
     </div>
   );
 }

 function ExpensesTab() {
+  const { t } = useTranslation();
   return (
     <div className="flex flex-col gap-2 py-2">
       {demoPayments.map((payment) => (
-        <div key={payment.label} ...>
+        <div key={payment.labelKey} ...>
           <span className="text-primary">
-            {payment.emoji} {payment.label}
+            {payment.emoji} {t(payment.labelKey)}
           </span>
```

```diff
 function SettlementsTab() {
+  const { t } = useTranslation();
   return (
     <div className="flex flex-col gap-2 py-2">
       {demoSettlements.map((settlement) => (
         <div key={`${settlement.from}-${settlement.to}`} ...>
           <span className="text-primary">
-            <span className="font-medium">{settlement.from}</span>{" "}
+            <span className="font-medium">
+              {settlement.from === "You" ? t("landing.demo.you") : settlement.from}
+            </span>{" "}
             <span className="text-secondary">→</span>{" "}
-            <span className="font-medium">{settlement.to}</span>
+            <span className="font-medium">
+              {settlement.to === "You" ? t("landing.demo.you") : settlement.to}
+            </span>
           </span>
           <div className="flex items-center gap-3">
             <span className="font-medium text-primary">
               {settlement.amount} zł
             </span>
             <span className={clsx(...)}>
-              {settlement.status === "confirmed" ? "Confirmed" : "Pending"}
+              {settlement.status === "confirmed"
+                ? t("landing.demo.status.confirmed")
+                : t("landing.demo.status.pending")}
             </span>
```

Top-level `TABS` array and section copy — move `TABS` inside the component (it now needs `t`):

```diff
-type TabId = "balance" | "expenses" | "members" | "settlements";
-
-const TABS: { id: TabId; label: string }[] = [
-  { id: "balance", label: "Balance" },
-  { id: "expenses", label: "Expenses" },
-  { id: "members", label: "Members" },
-  { id: "settlements", label: "Settlements" },
-];
+type TabId = "balance" | "expenses" | "members" | "settlements";
```

```diff
 export function InteractiveDemo() {
+  const { t } = useTranslation();
   const [activeTab, setActiveTab] = useState<TabId>("balance");
   const ActiveContent = TAB_CONTENT[activeTab];
+
+  const tabs: { id: TabId; label: string }[] = [
+    { id: "balance", label: t("stats.balance") },
+    { id: "expenses", label: t("landing.demo.tabs.expenses") },
+    { id: "members", label: t("member.list.title") },
+    { id: "settlements", label: t("settlement.list.title") },
+  ];
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            See your money clearly.
+            {t("landing.demo.title")}
           </h2>
           <p className="mt-4 text-lg text-secondary">
-            Everything important at a glance.
+            {t("landing.demo.subtitle")}
           </p>
```

```diff
           <div className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-bg p-1">
-            {TABS.map((tab) => (
+            {tabs.map((tab) => (
```

- [ ] **Step 4: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/landing/mock-data.ts frontend/components/landing/HeroDashboard.tsx frontend/components/landing/InteractiveDemo.tsx
git commit -m "feat(i18n): translate hero dashboard mockup and interactive demo"
```

---

## Task 16: Wire `ProblemSection` + `HowItWorks` + `ProductShowcase`

**Files:**
- Modify: `frontend/components/landing/ProblemSection.tsx`
- Modify: `frontend/components/landing/HowItWorks.tsx`
- Modify: `frontend/components/landing/ProductShowcase.tsx`
- Modify: `frontend/components/landing/mock-data.ts` (remove now-unused `demoRoomName` export)

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `landing.problem.*`, `landing.howItWorks.*`, `landing.showcase.*`, `landing.demo.roomName`, `landing.demo.status.active`, `stats.balance`, `member.list.title` (Task 2).

- [ ] **Step 1: Wire `ProblemSection.tsx`**

```diff
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
```

```diff
 export function ProblemSection() {
+  const { t } = useTranslation();
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            Shared expenses shouldn&apos;t be complicated.
+            {t("landing.problem.title")}
           </h2>
           <p className="mt-4 text-lg leading-relaxed text-secondary">
-            You paid for dinner. Someone bought groceries. Another person
-            paid the rent. And now&nbsp;&mdash; who owes whom?
+            {t("landing.problem.subtitle")}
           </p>
```

```diff
               <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
-                Without Rexab
+                {t("landing.problem.withoutRexab")}
               </p>
```

```diff
               <p className="text-xs font-semibold uppercase tracking-wide text-accent">
-                With Rexab
+                {t("landing.problem.withRexab")}
               </p>
```

- [ ] **Step 2: Wire `HowItWorks.tsx`**

```diff
 import { Home, Receipt, CheckCircle2 } from "lucide-react";
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
-
-const steps = [
-  {
-    number: "01",
-    icon: Home,
-    title: "Create a room",
-    description: "Create a space for your apartment, trip or group.",
-  },
-  {
-    number: "02",
-    icon: Receipt,
-    title: "Add expenses",
-    description: "Record who paid and who should share the cost.",
-  },
-  {
-    number: "03",
-    icon: CheckCircle2,
-    title: "Settle up",
-    description: "Rexab calculates who owes whom and tracks repayments.",
-  },
-];
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function HowItWorks() {
+  const { t } = useTranslation();
+
+  const steps = [
+    {
+      number: "01",
+      icon: Home,
+      title: t("landing.howItWorks.step1.title"),
+      description: t("landing.howItWorks.step1.description"),
+    },
+    {
+      number: "02",
+      icon: Receipt,
+      title: t("landing.howItWorks.step2.title"),
+      description: t("landing.howItWorks.step2.description"),
+    },
+    {
+      number: "03",
+      icon: CheckCircle2,
+      title: t("landing.howItWorks.step3.title"),
+      description: t("landing.howItWorks.step3.description"),
+    },
+  ];
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            How Rexab works.
+            {t("landing.howItWorks.title")}
           </h2>
           <p className="mt-4 text-lg text-secondary">
-            Three simple steps. No spreadsheets. No calculations.
+            {t("landing.howItWorks.subtitle")}
           </p>
```

- [ ] **Step 3: Wire `ProductShowcase.tsx`**

```diff
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
 import {
   demoMemberBalances,
   demoMembers,
-  demoRoomName,
   demoTotalExpenses,
 } from "@/components/landing/mock-data";
```

```diff
 export function ProductShowcase() {
+  const { t } = useTranslation();
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            Stop doing math in group chats.
+            {t("landing.showcase.title")}
           </h2>
           <p className="mt-4 max-w-md text-lg leading-relaxed text-secondary">
-            Rexab keeps every shared expense, balance and settlement in
-            one place — so no one has to scroll back through messages to
-            remember who paid for what.
+            {t("landing.showcase.subtitle")}
           </p>
```

```diff
             <div className="flex items-center justify-between">
-              <p className="font-semibold text-primary">{demoRoomName}</p>
+              <p className="font-semibold text-primary">{t("landing.demo.roomName")}</p>
               <span className="rounded-full bg-positive-bg px-2.5 py-1 text-xs font-medium text-positive">
-                Active
+                {t("landing.demo.status.active")}
               </span>
             </div>

             <p className="mt-5 text-xs font-medium uppercase tracking-wide text-secondary">
-              Total expenses
+              {t("landing.showcase.totalExpenses")}
             </p>
```

```diff
             <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
-              Members
+              {t("member.list.title")}
             </p>
```

```diff
             <p className="text-xs font-semibold uppercase tracking-wide text-secondary">
-              Balance
+              {t("stats.balance")}
             </p>
```

- [ ] **Step 4: Remove the now-unused `demoRoomName` export from `mock-data.ts`**

```diff
-export const demoRoomName = "Apartment";
-
 export const demoMembers = ["Daniel", "Alex", "John", "Michael"];
```

- [ ] **Step 5: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean (lint would catch a leftover unused `demoRoomName` import if the removal in Step 4 were skipped).

- [ ] **Step 6: Commit**

```bash
git add frontend/components/landing/ProblemSection.tsx frontend/components/landing/HowItWorks.tsx frontend/components/landing/ProductShowcase.tsx frontend/components/landing/mock-data.ts
git commit -m "feat(i18n): translate problem section, how-it-works, product showcase"
```

---

## Task 17: Wire `Features` + `UseCases` + `TrustSection` + `Footer`

**Files:**
- Modify: `frontend/components/landing/Features.tsx`
- Modify: `frontend/components/landing/UseCases.tsx`
- Modify: `frontend/components/landing/TrustSection.tsx`
- Modify: `frontend/components/landing/Footer.tsx`

**Interfaces:**
- Consumes: `useTranslation` (Task 3), keys `landing.features.*`, `landing.demo.payments.*`, `landing.useCases.*`, `landing.trust.*`, `landing.footer.*`, `landing.nav.*` (Task 2), and `tList` for the three use-case item lists and the trust points list.

- [ ] **Step 1: Wire `Features.tsx`**

```diff
 import { Receipt, Users, CheckCircle2, LayoutDashboard } from "lucide-react";
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function Features() {
+  const { t } = useTranslation();
+
+  const expenseTags = [
+    { key: "landing.demo.payments.dinner", amount: "80 zł" },
+    { key: "landing.demo.payments.groceries", amount: "120 zł" },
+    { key: "landing.demo.payments.internet", amount: "40 zł" },
+  ];
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            Everything your group needs.
+            {t("landing.features.title")}
           </h2>
```

```diff
               <h3 className="mt-4 text-xl font-semibold text-primary">
-                Shared expenses
+                {t("landing.features.shared.title")}
               </h3>
               <p className="mt-2 max-w-md text-secondary">
-                Track every expense in one place, with who paid and who
-                owes what always visible.
+                {t("landing.features.shared.description")}
               </p>
               <div className="mt-6 flex flex-wrap gap-2">
-                {["Dinner · 80 zł", "Groceries · 120 zł", "Internet · 40 zł"].map(
-                  (item) => (
-                    <span key={item} ...>
-                      {item}
-                    </span>
-                  ),
-                )}
+                {expenseTags.map((tag) => (
+                  <span key={tag.key} ...>
+                    {t(tag.key)} · {tag.amount}
+                  </span>
+                ))}
               </div>
```

```diff
               <h3 className="mt-4 text-xl font-semibold text-primary">
-                Group management
+                {t("landing.features.group.title")}
               </h3>
               <p className="mt-2 text-secondary">
-                Manage members and permissions easily.
+                {t("landing.features.group.description")}
               </p>
```

```diff
               <h3 className="mt-4 text-xl font-semibold text-primary">
-                Easy settlements
+                {t("landing.features.settlements.title")}
               </h3>
               <p className="mt-2 text-secondary">
-                Keep track of who has paid you back.
+                {t("landing.features.settlements.description")}
               </p>
```

```diff
               <h3 className="mt-4 text-xl font-semibold text-primary">
-                Clear overview
+                {t("landing.features.overview.title")}
               </h3>
               <p className="mt-2 max-w-md text-secondary">
-                See balances and debts instantly, without digging
-                through chat history.
+                {t("landing.features.overview.description")}
               </p>
```

- [ ] **Step 2: Wire `UseCases.tsx`**

```diff
 import { Home, Plane, Users } from "lucide-react";
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
-
-const useCases = [
-  {
-    icon: Home,
-    title: "Roommates",
-    items: ["Rent", "Groceries", "Utilities", "Internet"],
-  },
-  {
-    icon: Plane,
-    title: "Trips",
-    items: ["Hotels", "Food", "Transport", "Tickets"],
-  },
-  {
-    icon: Users,
-    title: "Groups",
-    items: ["Events", "Parties", "Projects", "Activities"],
-  },
-];
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function UseCases() {
+  const { t, tList } = useTranslation();
+
+  const useCases = [
+    {
+      icon: Home,
+      title: t("landing.useCases.roommates.title"),
+      items: tList("landing.useCases.roommates.items"),
+    },
+    {
+      icon: Plane,
+      title: t("landing.useCases.trips.title"),
+      items: tList("landing.useCases.trips.items"),
+    },
+    {
+      icon: Users,
+      title: t("landing.useCases.groups.title"),
+      items: tList("landing.useCases.groups.items"),
+    },
+  ];
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            Wherever money is shared.
+            {t("landing.useCases.title")}
           </h2>
```

(the `useCases.map(...)` rendering below is unchanged — `title`/`items` are now pre-translated values instead of literals)

- [ ] **Step 3: Wire `TrustSection.tsx`**

```diff
 import { Check } from "lucide-react";
 import { Container } from "@/components/ui/Container";
 import { FadeIn } from "@/components/landing/FadeIn";
-
-const points = [
-  "Clear balances",
-  "Transparent settlements",
-  "Permission-based actions",
-  "One source of truth",
-  "Simple group management",
-];
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function TrustSection() {
+  const { t, tList } = useTranslation();
+  const points = tList("landing.trust.points");
+
   return (
```

```diff
           <h2 className="text-3xl font-semibold tracking-tight text-primary sm:text-4xl">
-            Built around clarity.
+            {t("landing.trust.title")}
           </h2>
```

```diff
           <p className="mx-auto mt-10 max-w-md text-sm text-secondary">
-            Every balance-changing action goes through a permission
-            check on the server — not the client — before it&apos;s
-            applied.
+            {t("landing.trust.footnote")}
           </p>
```

- [ ] **Step 4: Wire `Footer.tsx`**

```diff
 import Link from "next/link";
 import { Container } from "@/components/ui/Container";
-
-const columns = [
-  {
-    title: "Product",
-    links: [
-      { label: "How it works", href: "#how-it-works" },
-      { label: "Features", href: "#features" },
-      { label: "Use cases", href: "#use-cases" },
-    ],
-  },
-  {
-    title: "Resources",
-    links: [
-      { label: "Help", href: "#" },
-      { label: "Documentation", href: "#" },
-    ],
-  },
-  {
-    title: "Company",
-    links: [
-      { label: "About", href: "#" },
-      { label: "Contact", href: "#" },
-    ],
-  },
-  {
-    title: "Legal",
-    links: [
-      { label: "Privacy", href: "#" },
-      { label: "Terms", href: "#" },
-    ],
-  },
-];
+import { useTranslation } from "@/lib/i18n/LocaleProvider";
+
+("use client");
```

(Add `"use client";` as the real first line — this file currently has no directive and now calls a hook.)

```diff
 export function Footer() {
+  const { t } = useTranslation();
+
+  const columns = [
+    {
+      title: t("landing.footer.columns.product"),
+      links: [
+        { label: t("landing.nav.howItWorks"), href: "#how-it-works" },
+        { label: t("landing.nav.features"), href: "#features" },
+        { label: t("landing.nav.useCases"), href: "#use-cases" },
+      ],
+    },
+    {
+      title: t("landing.footer.columns.resources"),
+      links: [
+        { label: t("landing.footer.links.help"), href: "#" },
+        { label: t("landing.footer.links.documentation"), href: "#" },
+      ],
+    },
+    {
+      title: t("landing.footer.columns.company"),
+      links: [
+        { label: t("landing.footer.links.about"), href: "#" },
+        { label: t("landing.footer.links.contact"), href: "#" },
+      ],
+    },
+    {
+      title: t("landing.footer.columns.legal"),
+      links: [
+        { label: t("landing.footer.links.privacy"), href: "#" },
+        { label: t("landing.footer.links.terms"), href: "#" },
+      ],
+    },
+  ];
+
   return (
```

```diff
             <p className="mt-3 text-sm text-secondary">
-              Shared expenses. Simplified.
+              {t("landing.footer.tagline")}
             </p>
```

(`© 2026 Rexab` stays as-is — a copyright line with a brand name isn't translatable content.)

- [ ] **Step 5: Run the suite and lint**

Run: `npm test && npm run lint`
Expected: PASS, clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/landing/Features.tsx frontend/components/landing/UseCases.tsx frontend/components/landing/TrustSection.tsx frontend/components/landing/Footer.tsx
git commit -m "feat(i18n): translate features, use cases, trust section, footer"
```

---

## Task 18: Final verification

**Files:** none (verification only)

**Interfaces:** none.

- [ ] **Step 1: Run the full test suite**

Run (from `frontend/`): `npm test`
Expected: all test files PASS, including the parity test from Task 2.

- [ ] **Step 2: Run lint**

Run: `npm run lint`
Expected: clean — no unused imports (e.g. a leftover `demoRoomName`/`label` reference would show up here), no missing `"use client"` diagnostics.

- [ ] **Step 3: Start the dev server and manually verify in the browser**

Start the Next.js dev server (via the project's preview tooling) and check:
1. On the landing page (`/`), the `EN`/`RU` toggle in the navbar switches all visible copy (hero, problem section, how-it-works, features, use cases, trust section, interactive demo, final CTA, footer) between English and Russian with no console errors or hydration warnings.
2. Register or log in, and on `/dashboard`, `/rooms/[id]`, and `/settings`, toggle the switcher in the app shell header and confirm all copy switches, including the two pluralized member-count strings (check a room with 1 member and a room with 2+ members in Russian — expect "1 участник" vs "2 участника" vs "5 участников").
3. Reload the page after switching to Russian — the choice persists (no flash of English).
4. Open the browser devtools console — no `Missing translation for key` warnings.

- [ ] **Step 4: Report results**

No commit for this task — it's verification-only. If step 1-3 surface any issue, fix it as a follow-up commit referencing the task where the bug was introduced, then re-run this task's steps.
