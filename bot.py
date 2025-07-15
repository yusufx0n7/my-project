import asyncio
import aiohttp
import time
import logging
import json
import os
import math
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Konfiguratsiyalar ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# TOKEN va CHAT_ID (Bularni o'zingizning token va chat IDlaringiz bilan almashtiring)
TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU' # Bot tokeningizni shu yerga qo'ying
CHAT_IDS = ['7971306481', '6329050233']  # Chat ID lar ro'yxati (o'zingiznikini qo'ying)

MIN_VOLUME = 10000
MIN_PROFIT = 3
CHECKABLE_MIN = 1
CHECKABLE_MAX = 3
INVEST_AMOUNT = 200

# Ruxsat etilgan birjalar
ALLOWED_EXCHANGES = {  'SuperEx', 'CoinEx', 'Kraken', 'HTX', 'Toobit', 'AscendEX', 'Bitget',
    'BloFin', 'BDFI', 'Poloniex', 'BitMart', 'Bitrue', 'BYDFi', 'CoinW',
    'BingX', 'Ourbit', 'BTCC', 'WEEX', 'LBank', 'GMGN', 'KCEX',
    'DigiFinex', 'CoinCola', 'Binance', 'MEXC'
    }

# Kuzatiladigan koinlar (Nomlari) - SIZ BERGAN YANGI TAKRORLANMAGAN RO'YXAT
INITIAL_COIN_NAMES = [
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
    "Enjin Coin", "ARPA", "PlayDapp", "Cortex", "Nano", "Prom", "Reserve Rights",
    "Sui", "IOST", "SelfKey", "Flow", "Manta Network", "Tezos", "Bitcoin Cash",
    "Aptos", "Bitcoin Gold", "Dash", "Dent", "Lisk", "Firo", "PAX Gold", "eCash",
    "NEM", "Komodo", "Cosmos", "Solana", "Ocean Protocol", "Mask Network",
    "REI Network", "Streamr", "Viction", "Waves", "Automata Network", "Cyber",
    "Radworks", "API3", "Blur", "Gas", "Axelar", "Terra", "Galxe", "Decentraland",
    "Ardor", "Stacks", "ICON", "Golem", "WazirX", "Decred", "Steem", "Metal DAO",
    "NULS", "Flux", "Secret", "Biconomy", "COMBO", "Hedera", "Civic", "Request",
    "DeXe", "Origin Protocol", "MobileCoin", "Highstreet", "AVA (Travala)", "USD Coin",
    "Arweave", "Chiliz", "Harmony", "Storj", "TrueUSD", "PIVX", "IRISnet",
    "Basic Attention Token", "Metis", "Celestia", "NKN", "xMoney", "Marlin",
    "Wormhole", "QuarkChain", "Hooked Protocol", "Saga", "Astar", "Ark", "Tensor"
]

# Global o'zgaruvchilar
global_http_session: aiohttp.ClientSession = None
coin_info_map = {} # Koin nomlarini ID va simvollarga xaritalash {lower_name: {id: ..., symbol: ...}, lower_symbol: {id: ..., symbol: ...}}
EFFECTIVE_COIN_IDS = []  # Faqat IDsi topilgan koinlar
COIN_BATCHES = []        # Koinlarning bo'limlarga bo'lingan ro'yxati
current_batch_index = 0  # Hozirgi tekshirilayotgan bo'lim indeksi

COINS_LIST_FILE = 'coingecko_coins_list.json' # Koinlar ro'yxati saqlanadigan fayl

# Monitoring tsiklining davomiyligi (3 daqiqa = 180 soniya)
TOTAL_CYCLE_DURATION_SECONDS = 180

# Koinlarni bo'lish kerak bo'lgan jami bo'limlar soni
TOTAL_BATCHES = 3 # Sizning talabingiz bo'yicha

# CoinGecko bepul API uchun taxminiy minimal so'rovlar oralig'i (daqiqada 50-100 so'rov degan taxmin bilan)
COINGECKO_REQUEST_LIMIT_PER_MINUTE = 50 # CoinGecko bepul versiyasi uchun taxminiy limit
COINGECKO_DELAY_PER_REQUEST = 60 / COINGECKO_REQUEST_LIMIT_PER_MINUTE # 1.2 soniya/so'rov

# --- Yordamchi funksiyalar ---
async def send_telegram_message(text: str):
    """Telegramga xabar yuborish"""
    if not global_http_session:
        logger.error("Aiohttp session hali yaratilmagan!")
        return

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

    for chat_id in CHAT_IDS:
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        try:
            async with global_http_session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning(f"Telegramga xabar yuborishda xato. Status: {resp.status}, Javob: {await resp.text()}")
        except asyncio.TimeoutError:
            logger.error(f"Telegramga xabar yuborishda timeout ({chat_id}).")
        except aiohttp.ClientError as e:
            logger.error(f"Telegramga xabar yuborishda tarmoq xatosi ({chat_id}): {e}")
        except Exception as e:
            logger.error(f"Telegramga xabar yuborishda kutilmagan xato ({chat_id}): {e}")

# Kesh mexanizmi (avvalgi koddan olindi)
COIN_DATA_CACHE = {}
CACHE_EXPIRATION_SECONDS = 300 # 5 daqiqa keshda saqlash

async def fetch_tickers_data(session: aiohttp.ClientSession, coin_id: str, force_refresh: bool = False) -> dict:
    """
    CoinGecko API dan 'coins/{id}/tickers' endpointi orqali ma'lumotlarni olish.
    Arbitraj tahlili uchun zarur. Keshdan foydalanadi.
    API limitini bu yerda boshqarmaymiz, uni `monitor_loop` da batchlar orasida boshqaramiz.
    """
    current_time = time.time()
    if not force_refresh and coin_id in COIN_DATA_CACHE and \
       (current_time - COIN_DATA_CACHE[coin_id]['timestamp'] < CACHE_EXPIRATION_SECONDS):
        logger.debug(f"Keshdan yuklanmoqda: {coin_id}")
        return COIN_DATA_CACHE[coin_id]['data']

    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/tickers'
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                COIN_DATA_CACHE[coin_id] = {'data': data, 'timestamp': current_time}
                return data
            elif resp.status == 429: # Too Many Requests
                logger.warning(f"CoinGecko API limitiga yetildi (tickers endpoint - {coin_id}). Avtomatik kutish...")
                retry_after = int(resp.headers.get('Retry-After', '60'))
                await asyncio.sleep(retry_after + 1) # API tavsiya qilgan muddatdan sal ko'proq kutish
                return {"tickers": []} # Qayta urinish o'rniga bo'sh ma'lumot qaytaramiz
            else:
                logger.warning(f"Tickers API so'rovida xato ({coin_id}). Status: {resp.status}, Javob: {await resp.text()}")
                return {"tickers": []}
    except asyncio.TimeoutError:
        logger.error(f"Tickers API so'rovida timeout ({coin_id}).")
        return {"tickers": []}
    except aiohttp.ClientError as e:
        logger.error(f"Tickers API so'rovida tarmoq xatosi ({coin_id}): {e}")
        return {"tickers": []}
    except Exception as e:
        logger.error(f"Tickers API so'rovida kutilmagan xato ({coin_id}): {e}", exc_info=True)
        return {"tickers": []}

async def analyze_arbitrage_opportunity(session: aiohttp.ClientSession, coin_id: str, check_mode: bool = False):
    """
    Berilgan koin uchun arbitraj imkoniyatini tahlil qilish.
    Bu funksiya individual koin uchun 'tickers' endpointidan foydalanadi.
    """
    try:
        data = await fetch_tickers_data(session, coin_id)
        tickers = data.get("tickers", [])

        # Koin simvolini topish
        coin_symbol = ""
        # coin_info_map da koin ID bo'yicha qidirish
        for key, info in coin_info_map.items():
            if info.get('id') == coin_id:
                if info.get('symbol'):
                    coin_symbol = info['symbol'].upper()
                break
        if not coin_symbol: # Agar topilmasa, IDning birinchi qismini ishlatamiz
            coin_symbol = coin_id.split('-')[0].upper()


        filtered = [
            t for t in tickers
            if t.get("market", {}).get("name") in ALLOWED_EXCHANGES
            and t.get("target") == "USDT"
            and t.get("last") is not None and t.get("last") > 0
        ]

        if len(filtered) < 2:
            return

        buy = min(filtered, key=lambda x: x["last"])
        sell = max(filtered, key=lambda x: x["last"])

        buy_price = buy["last"]
        sell_price = sell["last"]

        buy_volume_usd = buy.get("converted_volume", {}).get("usd", 0)
        sell_volume_usd = sell.get("converted_volume", {}).get("usd", 0)

        if buy_volume_usd == 0 and buy.get('volume') is not None and buy_price > 0:
            buy_volume_usd = buy['volume'] * buy_price

        if sell_volume_usd == 0 and sell.get('volume') is not None and sell_price > 0:
            sell_volume_usd = sell['volume'] * sell_price

        volume = min(buy_volume_usd, sell_volume_usd) # USD dagi hajmni solishtirish

        if volume < MIN_VOLUME:
            return

        quantity = INVEST_AMOUNT / buy_price
        gross = quantity * sell_price
        net = gross - INVEST_AMOUNT # Foyda endi komissiyasiz hisoblanadi
        roi = (net / INVEST_AMOUNT) * 100

        # Agar foyda 20% dan yuqori bo'lsa, xabar yubormaslik (ma'lumot xatosi bo'lishi mumkin)
        if roi >= 20:
            logger.warning(f"Juda yuqori ROI topildi ({roi:.2f}%): {coin_id}. Yuborilmaydi (ma'lumot xatosi bo'lishi mumkin).")
            return

        if roi >= MIN_PROFIT and not check_mode:
            message = (
                f"🎉📈 **Qaynoq Arbitraj Imkoniyati Topildi!** 📈🎉\n\n"
                f"💰 **Koin:** {coin_id.replace('-', ' ').title()} ({coin_symbol})\n" # Koin nomini chiroyli qilish
                f"🔥 **Hajm (USD):** {volume:,.0f} USDT\n\n"
                f"⬇️ **Sotib olish:** {buy_price:.4f} @ **{buy['market']['name']}**\n"
                f"⬆️ **Sotish:** {sell_price:.4f} @ **{sell['market']['name']}**\n\n"
                f"💸 **Sof Foyda:** {net:.2f} USD\n"
                f"🚀 **ROI (Daromad):** {roi:.2f}%"
            )
            await send_telegram_message(message)
            logger.info(f"Arbitraj imkoniyati topildi va xabar yuborildi: {coin_id} ({coin_symbol}), ROI: {roi:.2f}%")

        elif check_mode and CHECKABLE_MIN <= roi < CHECKABLE_MAX:
            message = (
                f"🔎 **Tekshiruv Natijasi:** {coin_id.replace('-', ' ').title()} ({coin_symbol})\n\n" # Koin nomini chiroyli qilish
                f"⬇️ **Sotib olish:** {buy_price:.4f} @ **{buy['market']['name']}**\n"
                f"⬆️ **Sotish:** {sell_price:.4f} @ **{sell['market']['name']}**\n"
                f"🚀 **ROI (Daromad):** {roi:.2f}%"
            )
            await send_telegram_message(message)
            logger.info(f"Tekshiruv xabari yuborildi: {coin_id} ({coin_symbol}), ROI: {roi:.2f}%")

    except Exception as e:
        logger.error(f"⚠️ Arbitraj tahlilida kutilmagan xato ({coin_id}): {e}", exc_info=True)


async def get_or_load_coin_list(session: aiohttp.ClientSession):
    """
    CoinGecko'dan koinlar ro'yxatini yuklaydi yoki fayldan o'qiydi.
    Faqat bir marta, bot ishga tushganda chaqirilishi kerak.
    """
    if os.path.exists(COINS_LIST_FILE):
        logger.info(f"'{COINS_LIST_FILE}' faylidan koinlar ro'yxati yuklanmoqda. 🔄")
        with open(COINS_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.info("CoinGecko API dan koinlar ro'yxati olinmoqda (birinchi marta). 🌐")
        url = "https://api.coingecko.com/api/v3/coins/list"
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    with open(COINS_LIST_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    logger.info(f"Koinlar ro'yxati '{COINS_LIST_FILE}' fayliga saqlandi. ✅")
                    return data
                else:
                    logger.error(f"Coin list olishda xato. Status: {resp.status}, Javob: {await resp.text()} ❌")
                    return []
        except Exception as e:
            logger.error(f"Coin list olishda kutilmagan xato: {e} ⛔")
            return []

async def init_coin_ids():
    """Bot ishga tushganda koin nomlarini IDlarga va simvollarga tarjima qilish"""
    global coin_info_map, EFFECTIVE_COIN_IDS, COIN_BATCHES

    full_coin_list = await get_or_load_coin_list(global_http_session)
    for coin_entry in full_coin_list:
        # Nom bo'yicha xaritalash
        coin_info_map[coin_entry['name'].lower()] = {
            'id': coin_entry['id'],
            'symbol': coin_entry.get('symbol', '').upper() # Simvolni katta harflarga o'girish
        }
        # Simvol bo'yicha xaritalash (agar mavjud bo'lsa va takrorlanmasa)
        if coin_entry.get('symbol'):
            symbol_lower = coin_entry['symbol'].lower()
            # Agar bir xil simvolga ega bo'lgan boshqa koin nomi allaqachon mavjud bo'lmasa, uni qo'shamiz
            if symbol_lower not in coin_info_map or coin_info_map[symbol_lower]['id'] != coin_entry['id']:
                coin_info_map[symbol_lower] = {
                    'id': coin_entry['id'],
                    'symbol': coin_entry['symbol'].upper()
                }


    found_count = 0
    not_found_names = []
    # INITIAL_COIN_NAMES ro'yxatidan foydalanamiz
    for name_or_symbol in INITIAL_COIN_NAMES:
        coin_data = coin_info_map.get(name_or_symbol.lower())
        if coin_data:
            coin_id = coin_data['id']
            if coin_id not in EFFECTIVE_COIN_IDS: # Takrorlanmaslik uchun
                EFFECTIVE_COIN_IDS.append(coin_id)
                found_count += 1
        else:
            not_found_names.append(name_or_symbol)

    logger.info(f"Topilgan koin IDlari soni: {found_count} / {len(INITIAL_COIN_NAMES)} 🎯")
    if not_found_names:
        logger.warning(f"CoinGecko'da topilmagan koin nomlari/simvollari: {', '.join(not_found_names[:10])}{'...' if len(not_found_names) > 10 else ''} ⚠️")

    # Koinlar ro'yxati yuklangandan so'ng, bo'limlarga bo'lish
    if EFFECTIVE_COIN_IDS:
        COIN_BATCHES = get_coin_batches(EFFECTIVE_COIN_IDS, TOTAL_BATCHES)
        if not COIN_BATCHES:
            logger.error("Koin bo'limlari yaratilmadi, EFFECTIVE_COIN_IDS bo'sh bo'lishi mumkin. ⛔")
        else:
            logger.info(f"Koinlar {len(COIN_BATCHES)} ta bo'limga bo'lindi. Har bir bo'limda taxminan {len(COIN_BATCHES[0]) if COIN_BATCHES else 0} ta koin bor. ✨")


def get_coin_batches(all_coin_ids: list, num_batches: int) -> list[list]:
    """
    Koin IDlarini belgilangan sonli bo'limlarga teng taqsimlaydi.
    """
    if not all_coin_ids or num_batches <= 0:
        return []

    total_coins = len(all_coin_ids)
    if total_coins == 0:
        return []

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    effective_num_batches = num_batches
    batch_size = math.ceil(total_coins / effective_num_batches)
    logger.info(f"Har bir bo'limda taxminan {batch_size} ta koin bo'ladi. 📦")
    if batch_size > COINGECKO_REQUEST_LIMIT_PER_MINUTE:
        logger.warning(f"Har bir bo'limdagi koinlar soni ({batch_size}) CoinGecko'ning daqiqadagi taxminiy limitidan ({COINGECKO_REQUEST_LIMIT_PER_MINUTE}) oshib ketishi mumkin. Limitga duch kelishi ehtimoli bor. 🚨")

    batches = list(chunk_list(all_coin_ids, batch_size))
    return batches

async def monitor_loop():
    """
    Asosiy monitoring tsikli - koinlarni bo'linmalarga bo'lib, aylanma tartibda tekshirish.
    """
    global EFFECTIVE_COIN_IDS, current_batch_index, COIN_BATCHES

    while not EFFECTIVE_COIN_IDS:
        logger.info("Koinlar ro'yxati yuklanishini kutilmoqda... ⏳")
        await asyncio.sleep(5)
        if not EFFECTIVE_COIN_IDS:
            await init_coin_ids()

    if not COIN_BATCHES:
        logger.error("Koin bo'limlari yaratilmadi. Tekshiruvni boshlash mumkin emas. ⛔")
        return

    while True:
        start_scan_time = time.time()
        logger.info(f"🔍 Coinlarni skanerlash boshlandi ({time.strftime('%Y-%m-%d %H:%M:%S')})")

        if current_batch_index >= len(COIN_BATCHES):
            current_batch_index = 0

        current_batch_ids = COIN_BATCHES[current_batch_index]

        tasks = []
        for coin_id in current_batch_ids:
            tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id))

        if tasks:
            await asyncio.gather(*tasks)
            expected_min_delay_for_batch = len(current_batch_ids) * COINGECKO_DELAY_PER_REQUEST
            elapsed_time_for_batch_processing = time.time() - start_scan_time

            time_to_wait_for_api_limit = expected_min_delay_for_batch - elapsed_time_for_batch_processing
            if time_to_wait_for_api_limit > 0:
                logger.info(f"API limitini saqlash uchun {time_to_wait_for_api_limit:.2f} soniya kutish... ⏳")
                await asyncio.sleep(time_to_wait_for_api_limit)


        end_scan_time = time.time()
        scan_duration = end_scan_time - start_scan_time
        logger.info(f"✅ Bu bo'limdagi {len(current_batch_ids)} ta koin tekshirildi. Davomiyligi: {scan_duration:.2f} soniya. ")

        current_batch_index += 1

        if current_batch_index == len(COIN_BATCHES):
            cycle_completion_time = time.time() - (start_scan_time - scan_duration)
            remaining_time_for_cycle = TOTAL_CYCLE_DURATION_SECONDS - cycle_completion_time

            if remaining_time_for_cycle > 0:
                logger.info(f"⏳ To'liq aylanish yakunlanishiga {remaining_time_for_cycle:.0f} soniya qoldi. Kutish...")
                await asyncio.sleep(remaining_time_for_cycle)
            else:
                logger.warning(f"Monitoringning to'liq aylanishi kutilganidan uzoqroq davom etdi ({cycle_completion_time:.2f}s). Yangi aylanish darhol boshlanadi. ⚡")
            current_batch_index = 0
        else:
            pass


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    await update.message.reply_html(
        "👋 **Assalomu alaykum, Arbitraj Botiga xush kelibsiz!**\n\n"
        "Men 24/7 rejimida bozorlarni kuzatib, siz uchun eng yaxshi arbitraj imkoniyatlarini izlayman. "
        "Har bir topilgan imkoniyat haqida sizga darhol xabar beraman!\n\n"
        "👉 `/check` - Hozirgi arbitraj holatini tekshirish uchun ushbu buyruqdan foydalaning. 📊"
    )
    logger.info(f"'{update.effective_user.full_name}' (/start) buyrug'ini ishlatdi. ▶️")

async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check komandasi"""
    await update.message.reply_text("🔍 Tekshiruv boshlandi... Biroz kuting. Natijalar alohida xabar sifatida yuboriladi (agar topilsa). ⏳")
    logger.info(f"'{update.effective_user.full_name}' (/check) buyrug'ini ishlatdi. ✅")

    if not EFFECTIVE_COIN_IDS:
        await update.message.reply_text("Koinlar ro'yxati hali yuklanmadi yoki bo'sh. Bir ozdan so'ng qayta urinib ko'ring. 😔")
        logger.warning("Check buyrug'i berilganda koinlar ro'yxati bo'sh. ⚠️")
        return

    tasks = []
    # 50 tadan oshmasligi yoki jami koinlar soni, qaysi biri kichik bo'lsa
    COINS_TO_CHECK_FOR_COMMAND = min(50, len(EFFECTIVE_COIN_IDS))

    checked_count = 0
    start_check_time = time.time()
    for coin_id in EFFECTIVE_COIN_IDS:
        if checked_count >= COINS_TO_CHECK_FOR_COMMAND:
            break

        tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id, check_mode=True))
        checked_count += 1

    if tasks:
        await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_check_time
        expected_min_time = checked_count * COINGECKO_DELAY_PER_REQUEST
        time_to_wait = expected_min_time - elapsed_time
        if time_to_wait > 0:
            logger.info(f"'/check' buyrug'i uchun API limitini saqlash maqsadida {time_to_wait:.2f} soniya kutish. 🕰️")
            await asyncio.sleep(time_to_wait)


    await update.message.reply_text("✅ Tekshiruv yakunlandi! Natijalar yuqoridagi xabarlarda yuborilgan bo'lishi mumkin. 🎉")
    logger.info("Tekshiruv yakunlandi. 👍")

async def start_bot():
    """Botni ishga tushirish"""
    global global_http_session
    global_http_session = aiohttp.ClientSession()

    await init_coin_ids()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("check", check_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("Telegram bot ishga tushirildi. 🟢")

    asyncio.create_task(monitor_loop())

    try:
        while True:
            await asyncio.sleep(3600) # Botni doimiy ishlashini ta'minlash
    finally:
        if global_http_session:
            await global_http_session.close()
            logger.info("Aiohttp session yopildi. 🔴")
        logger.info("Telegram bot o'chirildi. 🛑")


async def main():
    """Asosiy funksiya: botni qayta-qayta ishga tushiradi"""
    while True:
        try:
            logger.info(f"\n🚀 Bot ishga tushirilmoqda ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            await start_bot()
        except Exception as e:
            logger.critical(f"❌ Botda halokatli xato yuz berdi va to'xtatildi: {e}", exc_info=True)
            await send_telegram_message(f"🆘 Bot to'xtatildi! Halokatli xato: <code>{e}</code> Iltimos, loglarni tekshiring.")
            logger.info("♻️ 30 soniyadan keyin qayta ishga tushirilmoqda...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN' or not CHAT_IDS or 'YOUR_CHAT_ID_1' in CHAT_IDS:
        logger.error("❌ Xatolik: TELEGRAM_TOKEN yoki CHAT_IDS konfiguratsiyasi to'g'ri emas. Iltimos, kod ichida ularni o'zgartiring.")
        print("\n" * 3)
        print("############################################################")
        print("#                                                          #")
        print("#  DIQQAT! TELEGRAM_TOKEN VA CHAT_IDS NI O'ZGARTIRING!    #")
        print("#  Yuqoridagi kodda `TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'`  #")
        print("#  va `CHAT_IDS = ['YOUR_CHAT_ID_1', 'YOUR_CHAT_ID_2']`   #")
        print("#  qatorlarini o'zingizning bot tokeningiz va chat IDlaringiz bilan almashtiring. #")
        print("#                                                          #")
        print("############################################################")
        print("\n" * 3)
        exit(1)

    print("""
    ################################################
    #                                              #
    #  24/7 Arbitraj Bot - Replitda doimiy ishlaydi #
    #                                              #
    ################################################
    """)
    logger.info(f"🤖 Bot tokeni: {'*' * (len(TELEGRAM_TOKEN) - 5)}{TELEGRAM_TOKEN[-5:]}")
    logger.info(f"👥 Xabar yuboriladigan chatlar: {', '.join(CHAT_IDS)}")
    logger.info(f"📋 Kuzatiladigan coinlar soni: {len(INITIAL_COIN_NAMES)} (dastlabki ro'yxat)")
    logger.info(f"📊 Jami {TOTAL_BATCHES} ta bo'limga bo'lingan.")
    logger.info(f"🔄 Har {TOTAL_CYCLE_DURATION_SECONDS/60:.0f} daqiqada yangi bo'lim tekshiruvi boshlanadi.")
    logger.info(f"⏰ Boshlanish vaqti: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot o'chirildi (KeyboardInterrupt). ⏹️")
    except Exception as e:
        logger.critical(f"Asyncio main loopda kutilmagan xato: {e}", exc_info=True)

