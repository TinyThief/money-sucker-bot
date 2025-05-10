from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# Главное меню
def build_main_menu():
    keyboard = [
        [InlineKeyboardButton("📈 Стратегии", callback_data="menu_strategies")],
        [InlineKeyboardButton("📊 Мониторинг", callback_data="menu_monitoring")],
        [InlineKeyboardButton("🛡 Управление рисками", callback_data="menu_risk")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню стратегий
def build_strategy_menu():
    keyboard = [
        [InlineKeyboardButton("▶️ Запустить стратегии", callback_data="start_strategies")],
        [InlineKeyboardButton("⏹ Остановить стратегии", callback_data="stop_strategies")],
        [InlineKeyboardButton("🔍 Активные сканирования", callback_data="scanning")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню мониторинга (с добавленным Heartbeat)
def build_monitoring_menu():
    keyboard = [
        [InlineKeyboardButton("📊 Проверить статус", callback_data="status")],
        [InlineKeyboardButton("📈 Открытые позиции", callback_data="positions")],
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("🛡 Heartbeat-статус", callback_data="heartbeat")],
        [InlineKeyboardButton("📚 Логи", callback_data="logs")],
        [InlineKeyboardButton("📉 Equity кривая", callback_data="equity_curve")],
        [InlineKeyboardButton("📊 Summary-график", callback_data="summary_plot")],
        [InlineKeyboardButton("📈 Символы (Winrate)", callback_data="symbol_stats")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню управления рисками
def build_risk_menu():
    keyboard = [
        [InlineKeyboardButton("🛡 Статус риска", callback_data="risk")],
        [InlineKeyboardButton("🔁 Повторные входы", callback_data="reentry")],
        [InlineKeyboardButton("📦 PnL-сводка", callback_data="pnl_summary")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню настроек
def build_settings_menu():
    keyboard = [
        [InlineKeyboardButton("📂 Загрузить веса", callback_data="load_weights")],
        [InlineKeyboardButton("🧠 Оптимизация confident весов", callback_data="optimize_confidence")],
        [InlineKeyboardButton("🔄 Автооптимизация confident", callback_data="optimize_confidence_auto")],
        [InlineKeyboardButton("📦 Версия бота", callback_data="version")],
        [InlineKeyboardButton("♻️ Перезапуск бота", callback_data="restart_bot")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

