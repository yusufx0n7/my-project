import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Konfiguratsiya
TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU'
TELEGRAM_CHAT_IDS = ['7971306481', '6329050233']

# Arbitraj foizlari
MINOR_ARBITRAGE_MIN = 1.0  # 1%
MINOR_ARBITRAGE_MAX = 3.0   # 3%
AUTO_ARBITRAGE_MIN = 3.0     # 3%
AUTO_ARBITRAGE_MAX = 25.0    # 25%
CHECK_INTERVAL = 60          # 60 sekund

# Koinlar ro'yxati
COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", 
    "DOT", "LINK", "MATIC", "SHIB", "TRX", "BCH", "LTC", "UNI",
    "ATOM", "XLM", "ETC", "XMR", "TON", "FIL", "APT", "HBAR",
    "NEAR", "VET", "ARB", "OP", "MNT", "IMX", "RNDR", "GRT",
    "AAVE", "STX", "EGLD", "THETA", "AXS", "XTZ", "SAND", "APE",
    "CHZ", "MANA", "GALA", "CRV", "LDO", "FXS", "KAVA", "RUNE",
    "NEO", "ZEC", "IOTA", "EOS", "KLAY", "FLOW", "ROSE", "WAVES",
    "DYDX", "COMP", "ENS", "GMT", "GNO", "BAT", "SNX", "SUSHI",
    "YFI", "1INCH", "ALGO", "ZIL", "ICX", "ONT", "QTUM", "SC",
    "ANKR", "STORJ", "OCEAN", "CELO", "REEF", "RSR", "COTI", "DENT",
    "HOT", "VTHO", "IOST", "PERP", "RLC", "UMA", "SXP", "ELF",
    "CVC", "POLY", "MTL", "SKL", "NKN", "OXT", "DIA", "BAND",
    "NMR", "LIT", "POWR", "FET", "RVN", "CTSI", "ACH", "STMX",
    "GLM", "SUPER", "CKB", "OGN", "RAD", "BAL", "JASMY", "SYS",
    "ANT", "MLN", "REQ", "NEST", "DATA", "ORN", "TRB", "MASK",
    "ALPHA", "QUICK", "AUDIO", "BADGER", "FIS", "POND", "DREP",
    "KEY", "ASR", "CELR", "TCT", "TKO", "MDT", "VITE", "TROY",
    "COS", "DEGO", "BEL", "CTK", "XVS", "CAKE", "BAKE", "BURGER",
    "SLP", "ALICE", "TLM", "BETA", "ATA", "GTC", "ERN", "KSM",
    "PHA", "MOVR", "GLMR", "SDN", "CLV", "KAR", "BNT", "JST",
    "SFP", "C98", "ID", "ADX", "VIB", "MBOX", "WAXP", "TWT",
    "REI", "GAL", "LEVER", "LINA", "EDU", "HOOK", "STG", "PEOPLE",
    "DUSK", "CVX", "AGIX", "RPL", "SSV", "HIGH", "MINA", "FLUX",
    "RVN", "DOCK", "PUNDIX", "VGX", "CELO", "PLA", "PYR", "RARE",
    "GOG", "DPR", "VRA", "SANTOS", "LAZIO", "PORTO", "ALPINE",
    "CITY", "OG", "ATM", "ASR", "JUV", "PSG", "ACM", "ARG",
    "CHESS", "DAR", "EPX", "FIDA", "HFT", "IQ", "JOE", "KDA",
    "LCX", "MAGIC", "NPT", "OOKI", "QI", "STRAX", "TIME", "UFO",
    "VELO", "WIN", "XCAD", "YGG", "ZEN", "ZRX"
]

# Birjalar ro'yxati
EXCHANGES = [
    "Binance", "Coinbase", "Kraken", "KuCoin", "HTX", "Bybit",
    "OKX", "Bitget", "MEXC", "Gate.io", "Bitfinex", "Gemini"
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self):
        self.application = None
        self.is_running = False
        self.start_time = None
        self.bot = Bot(token=TELEGRAM_TOKEN)

    async def send_message(self, chat_id: str, text: str, parse_mode="Markdown"):
        """Xabarni yuborish"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Xabar yuborishda xato (chat_id {chat_id}): {e}")

    async def find_arbitrage_opportunities(self) -> List[Dict]:
        """Arbitraj imkoniyatlarini topish (mock ma'lumotlar)"""
        opportunities = []
        
        for coin in random.sample(COINS, 10):  # 10 ta tasodifiy koin
            # Har bir koin uchun 3 ta tasodifiy birjadan narxlar
            prices = {
                exchange: random.uniform(1, 1000)
                for exchange in random.sample(EXCHANGES, 3)
            }
            
            if len(prices) < 2:
                continue
                
            min_price = min(prices.values())
            max_price = max(prices.values())
            profit_percent = ((max_price - min_price) / min_price) * 100
            
            if profit_percent >= MINOR_ARBITRAGE_MIN:
                opportunities.append({
                    'coin': coin,
                    'prices': prices,
                    'profit_percent': profit_percent,
                    'time': datetime.now().strftime('%H:%M:%S')
                })
        
        return opportunities

    async def format_arbitrage_message(self, opportunity: Dict, is_minor: bool = False) -> str:
        """Arbitraj xabarini formatlash"""
        coin = opportunity['coin']
        profit = opportunity['profit_percent']
        prices = opportunity['prices']
        time = opportunity['time']
        
        min_exchange, min_price = min(prices.items(), key=lambda x: x[1])
        max_exchange, max_price = max(prices.items(), key=lambda x: x[1])
        
        if is_minor:
            return (
                f"💡 *Kichik Arbitraj*: {coin} {profit:.2f}%\n"
                f"▸ Sotib olish: *{min_exchange}* (${min_price:.2f})\n"
                f"▸ Sotish: *{max_exchange}* (${max_price:.2f})\n"
                f"⏱ {time}"
            )
        elif profit >= 25:
            return (
                f"🚨🚨 *YUQORI FOYDA!* {coin} {profit:.2f}%\n"
                f"▸ Sotib olish: *{min_exchange}* (${min_price:.2f})\n"
                f"▸ Sotish: *{max_exchange}* (${max_price:.2f})\n"
                f"🔔 *DARHOL HARAKAT QILING!*"
            )
        else:
            return (
                f"🚀 *Arbitraj Topildi!* {coin} {profit:.2f}%\n"
                f"▸ Sotib olish: *{min_exchange}* (${min_price:.2f})\n"
                f"▸ Sotish: *{max_exchange}* (${max_price:.2f})\n"
                f"⏱ {time}"
            )

    async def check_arbitrage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check komandasi - 1-3% arbitrajlarni tekshiradi"""
        await update.message.reply_text("Kichik arbitrajlar tekshirilmoqda...")
        
        opportunities = await self.find_arbitrage_opportunities()
        minor_opportunities = [
            opp for opp in opportunities 
            if MINOR_ARBITRAGE_MIN <= opp['profit_percent'] < MINOR_ARBITRAGE_MAX
        ]
        
        if minor_opportunities:
            for opp in minor_opportunities[:3]:  # Max 3 ta xabar
                message = await self.format_arbitrage_message(opp, is_minor=True)
                await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(1)  # Flooddan saqlanish uchun
        else:
            await update.message.reply_text("ℹ️ Hozircha 1-3% oralig'ida arbitraj topilmadi")

    async def auto_check_arbitrage(self):
        """Avtomatik tekshiruv - 3-25% arbitrajlarni topadi"""
        if not self.is_running:
            return
            
        opportunities = await self.find_arbitrage_opportunities()
        auto_opportunities = [
            opp for opp in opportunities 
            if opp['profit_percent'] >= AUTO_ARBITRAGE_MIN
        ]
        
        if auto_opportunities:
            for opp in auto_opportunities:
                message = await self.format_arbitrage_message(opp)
                for chat_id in TELEGRAM_CHAT_IDS:
                    await self.send_message(chat_id, message)
                    await asyncio.sleep(1)  # Flooddan saqlanish uchun

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start komandasi"""
        welcome_msg = """
🤖 *Crypto Arbitrage Botga Xush Kelibsiz!* 🚀

🔍 *Bot qanday ishlaydi:*
- 3-25% arbitrajlarni avtomatik yuboradi
- 1-3% arbitrajlarni /check buyrug'i bilan ko'rishingiz mumkin

📊 *Foydali buyruqlar:*
/start - Bot haqida ma'lumot
/check - Kichik arbitrajlarni tekshirish
        """
        await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)

    async def run_bot(self):
        """Botni ishga tushirish va 24/7 ishlatish"""
        self.start_time = datetime.now()
        self.is_running = True
        
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Command handlerlar
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("check", self.check_arbitrage))
        
        # Avtomatik tekshiruvni ishga tushirish
        asyncio.create_task(self.auto_check_loop())
        
        logger.info("Bot ishga tushmoqda...")
        await self.application.run_polling()

    async def auto_check_loop(self):
        """Avtomatik tekshiruv tsikli"""
        while self.is_running:
            try:
                await self.auto_check_arbitrage()
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Avtomatik tekshiruvda xato: {e}")
                await asyncio.sleep(30)

    async def stop_bot(self):
        """Botni to'xtatish"""
        self.is_running = False
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        logger.info("Bot to'xtatildi")

async def main():
    bot = ArbitrageBot()
    try:
        await bot.run_bot()
    except KeyboardInterrupt:
        await bot.stop_bot()
    except Exception as e:
        logger.error(f"Xato yuz berdi: {e}")
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())