/**
 * Static demo data for the marketing page only. None of this touches
 * the real API — it exists purely to render realistic-looking product
 * mockups. Shapes loosely mirror types/api.ts so swapping in a real
 * dashboard response later is a straight substitution.
 */

export const demoMembers = ["Daniel", "Alex", "John", "Michael"];

export const demoBalance = {
  balance: 230,
  youOwe: 120,
  youAreOwed: 350,
};

export const demoTransfers = [
  { from: "Alex", to: "You", amount: 120 },
  { from: "John", to: "Alex", amount: 50 },
];

export const demoPayments = [
  { labelKey: "landing.demo.payments.dinner", emoji: "🍕", amount: 80 },
  { labelKey: "landing.demo.payments.groceries", emoji: "🛒", amount: 120 },
  { labelKey: "landing.demo.payments.internet", emoji: "📶", amount: 40 },
  { labelKey: "landing.demo.payments.utilities", emoji: "💡", amount: 180 },
];

export const demoMemberBalances = [
  { name: "Daniel", balance: 230 },
  { name: "Alex", balance: -80 },
  { name: "John", balance: -150 },
];

export const demoSettlements = [
  { from: "Alex", to: "You", amount: 50, status: "pending" as const },
  { from: "John", to: "Alex", amount: 30, status: "confirmed" as const },
];

export const demoTotalExpenses = demoPayments.reduce(
  (sum, payment) => sum + payment.amount,
  0,
);
