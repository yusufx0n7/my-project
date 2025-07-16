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
TELEGRAM_TOKEN ='7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU' # O'zingizning haqiqiy Telegram bot tokeningizni kiriting
TELEGRAM_CHAT_ID = '7971306481', '6329050233'      # O'zingizning haqiqiy Telegram chat ID'ingizni kiriting (raqam yoki string)

EXCHANGES = {
    'Binance', 'CoinEx', 'AscendEX', 'HTX', 'Bitget', 'Poloniex', 'BitMart',
    'Bitrue', 'BingX', 'MEXC', 'DigiFinex', 'SuperEx', 'CoinCola', 'Ourbit',
    'Toobit', 'BloFin', 'BDFI', 'BYDFi', 'CoinW', 'BTCC', 'WEEX', 'LBank',
    'GMGN', 'KCEX', 'Kraken'
}

# Umumiy bozor ma'lumotlari API nuqtalari.
# Haqiqiy birja arbitraji uchun har bir birjaning o'z API'siga ulanishingiz kerak.
API_ENDPOINTS = {
    'coinpaprika': 'https://api.coinpaprika.com/v1/tickers',
    'coincap': 'https://api.coincap.io/v2/assets',
    'coingecko': 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&per_page=250&page=1&sparkline=false&price_change_percentage=24h'
}

MIN_VOLUME_USD = 5000.0 # AQSH dollarida minimal 24 soatlik hajm
# Foyda foizi chegaralari
AUTO_SEND_MIN_PERCENT = 3.0
AUTO_SEND_MAX_PERCENT = 25.0
CHECK_VIA_COMMAND_MIN_PERCENT = 1.0
CHECK_VIA_COMMAND_MAX_PERCENT = 3.0 # Bu 3% gacha (eksklyuziv)

CHECK_INTERVAL_SECONDS = 180 # Avtomatik tekshiruv oralig'i (3 daqiqa)

# --- Boshlang'ich Tanga Ro'yxati ---
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

# --- Tanga ID xaritalash (JUDA MUHIM! Buni to'g'ri to'ldiring) ---
# Har bir tanga nomini turli APIlar ishlatadigan ID/simvollarga moslashtirish uchun.
# Misol:
COIN_MAPPING = {
    "Bitcoin": {"coinpaprika": "btc-bitcoin", "coincap": "bitcoin", "coingecko": "bitcoin", "symbol": "BTC"},
    "Ethereum": {"coinpaprika": "eth-ethereum", "coincap": "ethereum", "coingecko": "ethereum", "symbol": "ETH"},
    "Cardano": {"coinpaprika": "ada-cardano", "coincap": "cardano", "coingecko": "cardano", "symbol": "ADA"},
    # Qolgan tangalarni shu yerga qo'shing. Agar API ma'lumotida tanga bo'lmasa, uni qoldiring
    # yoki "None" deb belgilang.
}

# COIN_MAPPING lug'atini barcha INITIAL_COIN_NAMES_GROUP_1 tangalari bilan to'ldirish
# (Faqat joy egasi. Buni haqiqiy API IDlari bilan almashtirishingiz kerak!)
for coin_name in INITIAL_COIN_NAMES_GROUP_1:
    if coin_name not in COIN_MAPPING:
        symbol = "".join([word[0] for word in coin_name.split()]).upper() if len(coin_name.split()) > 1 else coin_name.upper()
        if " " in coin_name:
            id_slug = coin_name.lower().replace(" ", "-").replace("[new]", "").replace("[-]", "")
        else:
            id_slug = coin_name.lower()

        COIN_MAPPING[coin_name] = {
            "coinpaprika": f"{id_slug}-dummy", # Haqiqiy IDga almashtiring
            "coincap": id_slug,
            "coingecko": id_slug,
            "symbol": symbol
        }


# --- Logger sozlamalari ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Global ma'lumot saqlash joylari ---
# {tanga_nomi: [api_manbai1, api_manbai2, ...]}
coin_api_availability: Dict[str, List[str]] = {}
# {api_manbai: [tanga_nomi1, tanga_nomi2, ...]}
api_coins_distribution: Dict[str, List[str]] = {}
# {tanga_symbol: {birja: {narx, hajm_24h}}}
current_coin_prices: Dict[str, Dict[str, Dict[str, float]]] = {}

# --- Yordamchi Funksiyalar ---

async def fetch_data_from_api(session: aiohttp.ClientSession, api_name: str, url: str) -> Union[List[Dict], Dict, None]:
    """Berilgan API nuqtasidan ma'lumotlarni oladi."""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
            logger.warning(f"Failed to fetch from {api_name} ({url}). Status: {response.status}")
            return None
    except aiohttp.ClientError as e:
        logger.warning(f"Network or client error fetching from {api_name} ({url}): {e}")
        return None
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching from {api_name} ({url})")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching from {api_name} ({url}): {e}")
        return None

async def check_api_for_coin(session: aiohttp.ClientSession, api_name: str, coin_name: str, api_id: str) -> bool:
    """Ma'lum bir API'da tanga ma'lumoti borligini tekshiradi."""
    # Bu funksiya asosan tanga mavjudligini tekshirish uchun.
    # API ID orqali bevosita tekshirish API'larning ishlashiga bog'liq.
    # Hozirda bu joy egasi.
    await asyncio.sleep(0.01) # Kichik kechikish
    return random.choice([True, False]) # Haqiqiy API chaqiruvlari bilan almashtiring!

async def initial_coin_api_check_and_distribute():
    """
    Bot ishga tushganda tangalarni 10 daqiqa davomida tekshiradi,
    qaysi manbalarda ma'lumot borligini aniqlaydi va teng taqsimlaydi.
    """
    logger.info("Bot ishga tushmoqda. Dastlabki tanga API tekshiruvi boshlandi (maksimal 10 daqiqa)...")
    start_time = time.time()
    
    global coin_api_availability
    global api_coins_distribution

    coin_api_availability = {}

    async with aiohttp.ClientSession() as session:
        check_tasks = []
        for coin_name in INITIAL_COIN_NAMES_GROUP_1:
            coin_ids = COIN_MAPPING.get(coin_name, {})
            for api_source_name in API_ENDPOINTS.keys():
                if api_id_for_coin := coin_ids.get(api_source_name):
                    check_tasks.append(
                        check_api_for_coin(session, api_source_name, coin_name, api_id_for_coin)
                    )
                else:
                    logger.debug(f"No {api_source_name} ID found for {coin_name}. Skipping API check for this pair.")

        try:
            results = await asyncio.wait_for(asyncio.gather(*check_tasks), timeout=600)
            
            task_idx = 0
            for coin_name in INITIAL_COIN_NAMES_GROUP_1:
                coin_ids = COIN_MAPPING.get(coin_name, {})
                for api_source_name in API_ENDPOINTS.keys():
                    if coin_ids.get(api_source_name):
                        if task_idx < len(results) and results[task_idx]:
                            coin_api_availability.setdefault(coin_name, []).append(api_source_name)
                        task_idx += 1
        except asyncio.TimeoutError:
            logger.warning("Dastlabki API tekshiruvi 10 daqiqadan so'ng vaqt tugadi. Ba'zi tangalar to'liq tekshirilmagan bo'lishi mumkin.")
        except Exception as e:
            logger.error(f"Dastlabki API tekshiruvi paytida xato yuz berdi: {e}")

    api_coins_distribution = {api: [] for api in API_ENDPOINTS.keys()}
    
    available_coins_for_distribution = [coin for coin, apis in coin_api_availability.items() if apis]
    
    if not available_coins_for_distribution:
        logger.error("Hech bir tanga uchun API ma'lumotlari topilmadi. Bot davom eta olmaydi.")
        return

    all_apis_for_distribution = list(API_ENDPOINTS.keys())
    if not all_apis_for_distribution:
        logger.error("Hech qanday API endpointlari konfiguratsiya qilinmagan. Taqsimlash mumkin emas.")
        return

    for coin_name in available_coins_for_distribution:
        apis_for_current_coin = coin_api_availability.get(coin_name, [])
        
        if not apis_for_current_coin:
            logger.warning(f"Tanga '{coin_name}' uchun hech qanday API topilmadi. O'tkazib yuborilmoqda.")
            continue

        chosen_api = None
        min_coins_on_api = float('inf')

        shuffled_apis_for_coin = list(apis_for_current_coin)
        random.shuffle(shuffled_apis_for_coin)

        for api in shuffled_apis_for_coin:
            if len(api_coins_distribution[api]) < min_coins_on_api:
                min_coins_on_api = len(api_coins_distribution[api])
                chosen_api = api
        
        if chosen_api:
            api_coins_distribution[chosen_api].append(coin_name)
        else:
            logger.warning(f"Tanga '{coin_name}' uchun API tanlashda xatolik. O'tkazib yuborilmoqda.")

    logger.info(f"Dastlabki tanga API tekshiruvi {time.time() - start_time:.2f} soniyada yakunlandi.")
    logger.info("Tangalarning API manbalari bo'yicha taqsimoti:")
    for api, coins in api_coins_distribution.items():
        logger.info(f"API '{api}': {len(coins)} ta tanga.")


# --- Telegram Bot Funksiyalari ---
async def send_telegram_message(text: str, is_creative: bool = False):
    """Telegram chatiga xabar yuboradi."""
    try:
        if is_creative:
            emojis = ['📈', '💰', '🚀', '✨', '🔥', '💎', '🎉', '🤑']
            creative_message = f"{random.choice(emojis)} *ARBITRAGE OPPORTUNITY ALERT!* {random.choice(emojis)}\n\n{text}\n\n_Don't miss out!_ {random.choice(emojis)}"
            await Bot(token=TELEGRAM_TOKEN).send_message(chat_id=TELEGRAM_CHAT_ID, text=creative_message, parse_mode=ParseMode.MARKDOWN)
        else:
            await Bot(token=TELEGRAM_TOKEN).send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Telegram xatosi: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start buyrug'iga javob beradi."""
    await update.message.reply_text("👋 Salom! Arbitraj botiga xush kelibsiz! 🚀💰💎\n"
                                    "Men har 3 daqiqada arbitraj imkoniyatlarini avtomatik tekshiraman.\n"
                                    "Agar foyda 3% dan 25% gacha bo'lsa, sizga darhol xabar beraman.\n"
                                    "Agar foyda 1% dan 3% gacha bo'lsa, /check buyrug'ini yuborib tekshirishingiz mumkin.\n"
                                    "Omad tilayman!")

async def check_arbitrage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check buyrug'iga javob beradi va faqat kichik arbitrajlarni yoki foydalanuvchi so'raganda barcha imkoniyatlarni tekshiradi."""
    await update.message.reply_text("Arbitraj imkoniyatlari tekshirilmoqda... Iltimos, kuting.")
    
    prices = await get_all_prices_from_distributed_apis()
    
    # Faqat 1% dan 3% gacha bo'lgan arbitrajlarni ko'rsatish
    messages = find_arbitrage(prices, check_only_minor=True)

    if messages:
        for msg in messages:
            await send_telegram_message(msg, is_creative=False) # Kichiklar uchun ijodiy emas
    else:
        await update.message.reply_text("Hozircha 1% dan 3% gacha bo'lgan kichik arbitraj imkoniyatlari topilmadi.")

    await update.message.reply_text("Tekshiruv yakunlandi.")


async def get_all_prices_from_distributed_apis() -> Dict[str, Dict[str, float]]:
    """
    Taqsimlangan API manbalaridan tanga narxlarini oladi.
    Bu yerda sizning haqiqiy API integratsiyangiz (CCXT bilan birjalar uchun) bo'lishi kerak.
    """
    collected_prices: Dict[str, Dict[str, float]] = {}
    async with aiohttp.ClientSession() as session:
        tasks = []
        for api_name, coins_to_fetch in api_coins_distribution.items():
            for coin_name in coins_to_fetch:
                coin_ids = COIN_MAPPING.get(coin_name, {})
                api_id = coin_ids.get(api_name)
                symbol = coin_ids.get("symbol", coin_name.upper()) # Umumiy symbol

                if api_id:
                    tasks.append(
                        fetch_mock_price_for_coin(session, api_name, api_id, symbol, coin_name)
                    )
        
        results = await asyncio.gather(*tasks)

        for result in results:
            if result:
                coin_symbol = result['symbol']
                api_source = result['source']
                price = result['price']
                volume = result['volume']

                if price is not None and volume >= MIN_VOLUME_USD:
                    collected_prices.setdefault(coin_symbol, {})[api_source] = price
                else:
                    logger.debug(f"Discarding {coin_symbol} from {api_source}: No valid price or low volume.")
    
    # --- Birjadan narxlarni olish (MUHIM QISM - CCXT bilan to'ldirish kerak) ---
    # Bu yerda siz CCXT yordamida har bir birjadan real narxlarni olishingiz kerak.
    # Hozircha bu joy egasi.
    for coin_name in INITIAL_COIN_NAMES_GROUP_1: # Barcha tangalarni tekshiramiz
        coin_symbol = COIN_MAPPING.get(coin_name, {}).get("symbol", coin_name.upper())
        for exchange in EXCHANGES:
            # Bu yerda siz CCXT yordamida real birja narxini olishingiz kerak
            # Misol: ticker = await ccxt.binance().fetch_ticker(f'{coin_symbol}/USDT')
            # va keyin collected_prices[coin_symbol][exchange] = ticker['last'] ni to'ldiring.
            
            # Hozircha mock data:
            mock_price = random.uniform(1000, 100000) if coin_symbol == "BTC" else random.uniform(0.1, 5000)
            mock_volume = random.uniform(MIN_VOLUME_USD, MIN_VOLUME_USD * 1000)
            if random.random() < 0.1: # 10% ehtimol bilan ba'zi birjalarda ma'lumot bo'lmasin
                mock_price = None
                mock_volume = 0
            
            if mock_price is not None and mock_volume >= MIN_VOLUME_USD:
                collected_prices.setdefault(coin_symbol, {})[exchange] = mock_price
            else:
                 logger.debug(f"Mock: Discarding {coin_symbol} on {exchange} due to no price or low volume.")

    return collected_prices

async def fetch_mock_price_for_coin(session: aiohttp.ClientSession, api_name: str, api_id: str, coin_symbol: str, coin_name: str) -> Dict[str, Union[str, float, None]]:
    """
    Bu funksiya API'dan real ma'lumot olishni simulyatsiya qiladi.
    Siz buni haqiqiy API chaqiruvlari bilan almashtirishingiz kerak!
    """
    await asyncio.sleep(random.uniform(0.1, 0.5)) # Tarmoq kechikishini simulyatsiya qilish
    
    price = random.uniform(0.01, 50000)
    volume = random.uniform(MIN_VOLUME_USD * 0.5, MIN_VOLUME_USD * 200)

    if random.random() < 0.05:
        return {'symbol': coin_symbol, 'source': api_name, 'price': None, 'volume': 0}

    return {'symbol': coin_symbol, 'source': api_name, 'price': price, 'volume': volume}


def find_arbitrage(prices: Dict[str, Dict[str, float]], check_only_minor: bool = False) -> List[str]:
    """
    Berilgan narx chegaralarida arbitraj imkoniyatlarini topadi.
    `check_only_minor` True bo'lsa, faqat 1%-3% gacha bo'lganlarni qaytaradi.
    """
    messages = []
    for coin_symbol, sources_data in prices.items():
        if len(sources_data) < 2:
            continue

        valid_prices = []
        for source, price in sources_data.items():
            if price is not None and price > 0:
                valid_prices.append({'source': source, 'price': price})

        if len(valid_prices) < 2:
            continue

        min_price_info = min(valid_prices, key=lambda x: x['price'])
        max_price_info = max(valid_prices, key=lambda x: x['price'])

        min_price = min_price_info['price']
        max_price = max_price_info['price']

        if min_price == 0:
            continue

        diff_percent = ((max_price - min_price) / min_price) * 100

        if check_only_minor: # Agar faqat kichik arbitrajlar so'ralgan bo'lsa
            if CHECK_VIA_COMMAND_MIN_PERCENT <= diff_percent < CHECK_VIA_COMMAND_MAX_PERCENT:
                messages.append(
                    f"💡 Kichik Arbitraj Ogohlantirishi: {coin_symbol.upper()} {diff_percent:.2f}% farq ko'rsatmoqda.\n"
                    f"Sotib olish: {min_price_info['source']} dan ${min_price:.4f}, sotish: {max_price_info['source']} dan ${max_price:.4f}"
                )
        else: # Avtomatik yuborish uchun (3%-25% oralig'i)
            if AUTO_SEND_MIN_PERCENT <= diff_percent <= AUTO_SEND_MAX_PERCENT:
                messages.append(
                    f"🚀 *Arbitraj Imkoniyati!* ({coin_symbol.upper()}) 🚀\n"
                    f"Sotib olish: *{min_price_info['source']}* dan ${min_price:.4f}\n"
                    f"Sotish: *{max_price_info['source']}* dan ${max_price:.4f}\n"
                    f"Potensial Foyda: *{diff_percent:.2f}%* 📈\n"
                    f"Vaqt: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
            elif diff_percent > AUTO_SEND_MAX_PERCENT:
                messages.append(
                    f"⚠️ *JUDA KATTA ARBITRAJ!* ({coin_symbol.upper()}) ⚠️\n"
                    f"Sotib olish: *{min_price_info['source']}* dan ${min_price:.4f}\n"
                    f"Sotish: *{max_price_info['source']}* dan ${max_price:.4f}\n"
                    f"Potensial Foyda: *{diff_percent:.2f}%* 🚨\n"
                    f"Vaqt: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                    f"_Darhol tekshiring!_ "
                )
    return messages

async def automatic_arbitrage_check():
    """Avtomatik ravishda arbitraj tekshiruvini amalga oshiradi va xabar yuboradi."""
    logger.info(f"Avtomatik arbitraj tekshiruvi boshlandi: {datetime.utcnow()}...")
    
    prices = await get_all_prices_from_distributed_apis()
    
    # Faqat avtomatik yuborish uchun mo'ljallangan arbitrajlarni qidirish
    messages = find_arbitrage(prices, check_only_minor=False)

    if messages:
        for msg in messages:
            await send_telegram_message(msg, is_creative=True)
    else:
        logger.info("Jiddiy arbitraj imkoniyatlari topilmadi (avtomatik tekshiruv).")

async def run_scheduler(application: Application):
    """Botning davriy ishlarini rejalashtiradi."""
    await application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="👋 Bot ishga tushdi va tangalarni dastlabki tekshiruvdan o'tkazmoqda. Iltimos kuting.")
    await initial_coin_api_check_and_distribute()
    await application.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Tangalarning dastlabki tekshiruvi va taqsimoti yakunlandi. Endi arbitraj imkoniyatlari har 3 daqiqada avtomatik tekshiriladi.")
    
    while True:
        await automatic_arbitrage_check()
        logger.info(f"Navbatdagi avtomatik tekshiruv {CHECK_INTERVAL_SECONDS} soniyadan so'ng...")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def main():
    """Botning asosiy ishga tushirish funksiyasi."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("check", check_arbitrage_command))

    # Botni ishga tushirgandan so'ng rejalashtiruvchini boshlash
    # run_polling() bilan birga ishlaydigan alohida task sifatida ishga tushiramiz
    asyncio.create_task(run_scheduler(application))

    logger.info("Telegram bot polling rejimida ishga tushmoqda...")
    await application.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
    except Exception as e:
        logger.critical(f"Asosiy tsiklda kutilmagan xato yuz berdi: {e}", exc_info=True)

