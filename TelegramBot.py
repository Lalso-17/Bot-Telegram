import logging
import requests
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === Logowanie ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Token ===
TELEGRAM_TOKEN = '7667255837:AAHWuVwiFx5xO-pRYLU04rqlj_E1DqHxFr4'

# === Ceny poprzednie ===
previous_prices = {}

# === Top 10 kryptowalut (Binance symbole) ===
crypto_map = {
    'BTCUSDT': 'Bitcoin',
    'ETHUSDT': 'Ethereum',
    'BNBUSDT': 'BNB',
    'SOLUSDT': 'Solana',
    'XRPUSDT': 'XRP',
    'DOGEUSDT': 'Dogecoin',
    'ADAUSDT': 'Cardano',
    'AVAXUSDT': 'Avalanche',
    'DOTUSDT': 'Polkadot',
    'MATICUSDT': 'Polygon'
}

# === Klawiatury ===
def get_start_keyboard():
    return ReplyKeyboardMarkup([['Start']], resize_keyboard=True)

def get_crypto_keyboard():
    return ReplyKeyboardMarkup([
        ['Bitcoin', 'Ethereum', 'BNB'],
        ['Solana', 'XRP', 'Dogecoin'],
        ['Cardano', 'Avalanche', 'Polkadot'],
        ['Polygon'],
        ['📊 Wszystkie kursy']
    ], resize_keyboard=True)

# === Pobieranie ceny z Binance ===
def get_price_from_binance(symbol):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    return round(float(data['price']), 2)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Naciśnij Start, aby rozpocząć 💸", reply_markup=get_start_keyboard())

# === Obsługa wiadomości ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lower_text = text.lower()
    chat_id = update.effective_chat.id
    logger.info(f"Wiadomość: {text}")

    if lower_text == 'start':
        await update.message.reply_text("Wybierz kryptowalutę z listy 💎:", reply_markup=get_crypto_keyboard())
        return

    if lower_text == '📊 wszystkie kursy':
        message = "📊 *Kursy kryptowalut:*\n\n"
        for symbol in crypto_map:
            try:
                price = get_price_from_binance(symbol)
                old_price = previous_prices.get(symbol)

                if old_price is not None:
                    emoji = "🔺" if price > old_price else "🔻" if price < old_price else "⏸"
                    message += f"{crypto_map[symbol]}: ${price:.2f} {emoji}\n"
                else:
                    message += f"{crypto_map[symbol]}: ${price:.2f}\n"

                previous_prices[symbol] = price
                time.sleep(1)

            except Exception as e:
                logger.warning(f"{symbol}: błąd pobierania — {e}")
                if symbol in previous_prices:
                    cached = previous_prices[symbol]
                    message += f"{crypto_map[symbol]}: ${cached:.2f} 🕒 (ostatnie dane)\n"
                else:
                    message += f"{crypto_map[symbol]}: ❌ Brak danych\n"

        await update.message.reply_text(message, parse_mode="Markdown")
        return

    # Obsługa jednej kryptowaluty
    symbol = next((key for key, val in crypto_map.items() if val.lower() == lower_text), None)
    if symbol:
        try:
            price = get_price_from_binance(symbol)
            old_price = previous_prices.get(symbol)

            if old_price is not None:
                emoji = "🔺" if price > old_price else "🔻" if price < old_price else "⏸"
                reply = f"{crypto_map[symbol]}: ${price:.2f} {emoji}"
            else:
                reply = f"{crypto_map[symbol]}: ${price:.2f}"

            previous_prices[symbol] = price
            await update.message.reply_text(f"💹 {reply}")

        except:
            if symbol in previous_prices:
                cached = previous_prices[symbol]
                await update.message.reply_text(f"💹 {crypto_map[symbol]}: ${cached:.2f} 🕒 (ostatnie dane)")
            else:
                await update.message.reply_text("❌ Nie udało się pobrać kursu")
    else:
        await update.message.reply_text("😕 Wybierz kryptowalutę z listy.", reply_markup=get_crypto_keyboard())

# === Start bota ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Bot uruchomiony")
    app.run_polling()
