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
  "room.page.codeLabel": "code",
  "room.page.toastSettlementRequested": "Settlement requested.",
  "room.page.toastPaymentConfirmed": "Payment confirmed.",
  "room.page.toastMemberRemoved": ({ name }) => `${name} removed from the room.`,
  "room.page.toastRoomDeleted": "Room deleted.",
  "room.page.toastLeftRoom": "You left the room.",
  "room.page.toastPaymentAdded": "Payment added.",

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
    "You paid for dinner. Someone bought groceries. Another person paid the rent. And now — who owes whom?",
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
