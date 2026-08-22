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
  "room.page.codeLabel": "код",
  "room.page.toastSettlementRequested": "Расчёт запрошен.",
  "room.page.toastPaymentConfirmed": "Платёж подтверждён.",
  "room.page.toastMemberRemoved": ({ name }) => `${name} удалён(а) из комнаты.`,
  "room.page.toastRoomDeleted": "Комната удалена.",
  "room.page.toastLeftRoom": "Вы покинули комнату.",
  "room.page.toastPaymentAdded": "Платёж добавлен.",

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
    "Вы заплатили за ужин. Кто-то купил продукты. Другой человек оплатил аренду. И теперь — кто кому должен?",
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
