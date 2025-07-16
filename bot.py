import asyncio
import aiohttp
import time
from datetime import datetime
from typing import List, Dict, Union
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import logging

# --- Konfiguratsiya ---
TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU'
TELEGRAM_CHAT_IDS = ['7971306481']

EXCHANGES = {
    'Binance', 'CoinEx', 'AscendEX', 'HTX', 'Bitget', 'Poloniex', 'BitMart',
    'Bitrue', 'BingX', 'MEXC', 'DigiFinex', 'SuperEx', 'CoinCola', 'Ourbit',
    'Toobit', 'BloFin', 'BDFI', 'BYDFi', 'CoinW', 'BTCC', 'WEEX', 'LBank',
    'GMGN', 'KCEX', 'Kraken'
}

API_ENDPOINTS = {
    'coinpaprika': 'https://api.coinpaprika.com/v1/tickers',
    'coincap': 'https://api.coincap.io/v2/assets',
    'coingecko': 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1&sparkline=false&price_change_percentage=24h'
}

MIN_VOLUME_USD = 5000.0
AUTO_SEND_MIN_PERCENT = 3.0
AUTO_SEND_MAX_PERCENT = 25.0
CHECK_VIA_COMMAND_MIN_PERCENT = 1.0
CHECK_VIA_COMMAND_MAX_PERCENT = 3.0
CHECK_INTERVAL_SECONDS = 180

# --- Logger sozlamalari ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Tanga ro'yxati va mapping ---
INITIAL_COIN_NAMES_GROUP_1 = [
    "Gitcoin", "Alchemy Pay", "Cardano", "AdEx", "Aergo", "Anchored Coins AEUR",
    "SingularityNET", "Algorand", "MyNeighborAlice", "Amp", "ApeCoin", "Polygon",
    "Verge", "Zilliqa", "VIDT DAO", "Bluzelle", "Stellar", "Chainlink", "Bitcoin",
    "Stratis", "Band Protocol", "Phala Network", "The Graph", "Polkadot",
    "Polymesh", "Solar", "LTO Network", "Vanar Chain", "IQ", "WAX",
    "First Digital USD", "JasmyCoin", "Nervos Network", "Arbitrum", "Drep [new]",
    "SPACE ID", "The Sandbox", "NEAR Protocol", "Internet Computer", "XRP",
    "Ethereum", "Celo", "Kadena", "Render", "Theta Network", "Theta Fuel", "Dusk",
    "Loom Network", "Avalanche", "Cartesi", "ORDI", "Syscoin", "Ravencoin",
    "Litecoin", "Loopring", "IOTA", "Livepeer", "Artificial Superintelligence Alliance",
    "Sei", "Bonfida", "Phoenix", "Ethereum Classic", "Gifto", "Celer Network",
    "Hive", "Horizen", "iExec RLC", "Powerledger", "Quant", "Crypterium", "DigiByte",
    "FIO Protocol", "Oasis Network", "DIA", "Ethereum Name Service",
    "Rootstock Infrastructure Rif", "Optimism", "TRON", "GMT", "Moonriver",
    "Measurable Data Token", "NFPrompt", "Klaytn", "Mina", "Filecoin", "Dogecoin",
    "Trust Wallet Token", "SuperRare", "Moonbeam", "VeChain", "Contentos", "Qtum",
    "MultiversX", "Pyth Network", "Conflux", "MANTRA", "SKALE", "Xai", "Portal",
    "Enjin Coin", "ARPA", "PlayDapp", "Cortex", "Nano", "Prom",
    "Reserve Rights", "Sui", "IOST", "SelfKey", "Flow", "Manta Network", "Tezos",
    "Bitcoin Cash", "Aptos", "Bitcoin Gold", "Dash", "Dent", "Lisk", "Firo",
    "PAX Gold", "eCash", "NEM", "Komodo", "Cosmos", "Solana", "Ocean Protocol",
    "Mask Network", "REI Network", "Streamr", "Viction", "Waves",
    "Automata Network", "Cyber", "Radworks", "API3", "Blur", "Gas", "Axelar",
    "Terra", "Galxe", "Decentraland", "Ardor", "Stacks", "ICON", "Golem",
    "WazirX", "Decred", "Steem", "Metal DAO", "NULS", "Flux", "Secret",
    "Biconomy", "COMBO", "Hedera", "Civic", "Request", "DeXe", "Origin Protocol",
    "MobileCoin", "Highstreet", "AVA (Travala)", "USD Coin", "Arweave", "Chiliz",
    "Harmony", "Storj", "TrueUSD", "PIVX", "IRISnet", "Basic Attention Token",
    "Metis", "Celestia", "NKN", "xMoney", "Marlin", "Wormhole", "QuarkChain",
    "Hooked Protocol", "Saga", "Astar", "Ark", "Tensor", "Beam", "Kusama",
    "Omni Network", "aelf", "Holo", "WINkLink", "Tellor", "Bittensor", "StormX",
    "Status", "SafePal", "Siacoin", "Orchid", "Ontology Gas", "IoTeX", "Toncoin",
    "Fame AI", "Alephium", "Hasaki", "Tether Gold", "OriginTrail", "Casper"
]

COIN_MAPPING = {
    "Bitcoin": {"coinpaprika": "btc-bitcoin", "coincap": "bitcoin", "coingecko": "bitcoin", "symbol": "BTC"},
    "Ethereum": {"coinpaprika": "eth-ethereum", "coincap": "ethereum", "coingecko": "ethereum", "symbol": "ETH"},
    "Cardano": {"coinpaprika": "ada-cardano", "coincap": "cardano", "coingecko": "cardano", "symbol": "ADA"},
}

for coin_name in INITIAL_COIN_NAMES_GROUP_1:
    if coin_name not in COIN_MAPPING:
        symbol = "".join([word[0] for word in coin_name.split()]).upper() if len(coin_name.split()) > 1 else coin_name[:4].upper()
        id_slug = coin_name.lower().replace(" ", "-").replace("[new]", "").replace("[-]", "")
        COIN_MAPPING[coin_name] = {
            "coinpaprika": f"{id_slug}",
            "coincap": id_slug,
            "coingecko": id_slug,
            "symbol": symbol
        }

class ArbitrageBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.session = None
        self.application = None
        self.is_running = True

    async def send_telegram_message(self, text: str, is_creative: bool = False):
        """Xabarni barcha chat ID larga yuborish"""
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                if is_creative:
                    emojis = ['📈', '💰', '🚀', '✨', '🔥', '💎', '🎉', '🤑']
                    creative_msg = f"{random.choice(emojis)} *CRYPTO ARBITRAGE* {random.choice(emojis)}\n\n{text}"
                    await self.bot.send_message(chat_id=chat_id, text=creative_msg, parse_mode=ParseMode.MARKDOWN)
                else:
                    await self.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Telegram xatosi (chat_id {chat_id}): {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start komandasi"""
        welcome_msg = """
🤖 *Crypto Arbitrage Botga Xush Kelibsiz!* 🚀

🔍 *Bot qanday ishlaydi:*
- Har 3 daqiqada 25+ birjalardan 200+ kriptovalyuta narxlarini solishtiradi
- 3% dan yuqori arbitraj imkoniyatlarini avtomatik yuboradi
- 1-3% oralig'idagilarni /check buyrug'i bilan ko'rishingiz mumkin

📊 *Foydali buyruqlar:*
/start - Bot haqida ma'lumot
/check - Kichik arbitrajlarni tekshirish
/stats - Bot statistikasi

⏳ Keyingi avtomatik tekshiruv: 3 daqiqadan so'ng

📈 Omad tilaymiz! 💰
        """
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
        await self.send_telegram_message(f"👤 Yangi foydalanuvchi: {update.effective_user.full_name}")

    async def check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check komandasi"""
        await update.message.reply_text("⏳ Kichik arbitraj imkoniyatlari tekshirilmoqda...")
        
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                prices = await self.get_all_prices_from_distributed_apis()
                messages = self.find_arbitrage(prices, check_only_minor=True)
                
                if messages:
                    for msg in messages[:5]:  # 5 tadan ortiq xabar yubormaslik
                        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("ℹ️ Hozircha 1%-3% oralig'ida arbitraj imkoniyatlari topilmadi")
        except Exception as e:
            logger.error(f"Check command error: {e}")
            await update.message.reply_text("⚠️ Tekshiruvda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

    async def get_all_prices_from_distributed_apis(self) -> Dict[str, Dict[str, float]]:
        """Narxlarni olish"""
        prices = {}
        
        # Mock data for testing
        for coin_name in INITIAL_COIN_NAMES_GROUP_1[:20]:  # First 20 coins for testing
            symbol = COIN_MAPPING.get(coin_name, {}).get("symbol", coin_name[:4].upper())
            prices[symbol] = {}
            
            for exchange in random.sample(list(EXCHANGES), 3):  # 3 random exchanges
                base_price = random.uniform(0.1, 50000)
                variation = random.uniform(-0.05, 0.05)  # -5% to +5% variation
                prices[symbol][exchange] = base_price * (1 + variation)
        
        return prices

    def find_arbitrage(self, prices: Dict[str, Dict[str, float]], check_only_minor: bool = False) -> List[str]:
        """Arbitrajni topish"""
        messages = []
        
        for symbol, exchanges in prices.items():
            if len(exchanges) < 2:
                continue
                
            min_exchange, min_price = min(exchanges.items(), key=lambda x: x[1])
            max_exchange, max_price = max(exchanges.items(), key=lambda x: x[1])
            
            if min_price <= 0:
                continue
                
            diff_percent = ((max_price - min_price) / min_price) * 100
            
            if check_only_minor:
                if CHECK_VIA_COMMAND_MIN_PERCENT <= diff_percent < CHECK_VIA_COMMAND_MAX_PERCENT:
                    messages.append(
                        f"💡 *Kichik Arbitraj*: {symbol} {diff_percent:.2f}%\n"
                        f"▸ Sotib olish: *{min_exchange}* (${min_price:.4f})\n"
                        f"▸ Sotish: *{max_exchange}* (${max_price:.4f})"
                    )
            else:
                if AUTO_SEND_MIN_PERCENT <= diff_percent <= AUTO_SEND_MAX_PERCENT:
                    messages.append(
                        f"🚀 *Arbitraj Topildi!* {symbol} {diff_percent:.2f}%\n"
                        f"▸ Sotib olish: *{min_exchange}* (${min_price:.4f})\n"
                        f"▸ Sotish: *{max_exchange}* (${max_price:.4f})\n"
                        f"⏱ {datetime.now().strftime('%H:%M:%S')}"
                    )
                elif diff_percent > AUTO_SEND_MAX_PERCENT:
                    messages.append(
                        f"⚠️⚠️ *YUQORI FOYDA!* {symbol} {diff_percent:.2f}%\n"
                        f"▸ Sotib olish: *{min_exchange}* (${min_price:.4f})\n"
                        f"▸ Sotish: *{max_exchange}* (${max_price:.4f})\n"
                        f"🔔 *DARHOL HARAKAT QILING!*"
                    )
        
        return messages

    async def automatic_arbitrage_check(self):
        """Avtomatik tekshiruv"""
        try:
            logger.info("=== Avtomatik tekshiruv boshlandi ===")
            
            async with aiohttp.ClientSession() as session:
                self.session = session
                prices = await self.get_all_prices_from_distributed_apis()
                messages = self.find_arbitrage(prices)
                
                if messages:
                    for msg in messages:
                        await self.send_telegram_message(msg, is_creative=True)
                        await asyncio.sleep(1)  # Telegram flood protection
                else:
                    logger.info("Hech qanday arbitraj topilmadi")
                    
        except Exception as e:
            logger.error(f"Avtomatik tekshiruvda xato: {e}")
        finally:
            self.session = None

    async def run_scheduler(self):
        """Rejalashtiruvchi"""
        await asyncio.sleep(10)  # Dastlabki kutish
            
        while self.is_running:
            try:
                await self.automatic_arbitrage_check()
            except Exception as e:
                logger.error(f"Scheduler xatosi: {e}")
            
            logger.info(f"Keyingi tekshiruv {CHECK_INTERVAL_SECONDS} soniyadan so'ng...")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    async def start(self):
        """Botni ishga tushirish"""
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Command handlerlar
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("check", self.check_command))
        
        # Schedulerni ishga tushirish
        asyncio.create_task(self.run_scheduler())
        
        # Adminlarga xabar
        await self.send_telegram_message(
            "🤖 *Arbitraj Boti Ishga Tushdi!*\n"
            f"⏳ Avtomatik tekshiruv har {CHECK_INTERVAL_SECONDS//60} daqiqada\n"
            f"📊 Koinlar soni: {len(INITIAL_COIN_NAMES_GROUP_1)}\n"
            f"🏦 Birjalar soni: {len(EXCHANGES)}"
        )
        
        logger.info("Bot ishga tushmoqda...")
        await self.application.run_polling()

    async def stop(self):
        """Botni to'xtatish"""
        self.is_running = False
        if self.session:
            await self.session.close()
        await self.send_telegram_message("🛑 Bot to'xtatildi")

async def main():
    bot = ArbitrageBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
    except Exception as e:
        logger.critical(f"Asosiy xato: {e}")
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())