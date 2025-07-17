import asyncio, aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# === CONFIG ===

TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU'
# ADMIN_TELEGRAM_ID endi to'g'ri tuple sifatida belgilangan.
ADMIN_TELEGRAM_ID = (7971306481, 6329050233)  # Raqamlarni int qilib kiriting.

ALLOWED_EXCHANGES = set([
    'Binance', 'CoinEx', 'AscendEX', 'HTX', 'Bitget', 'Poloniex', 'BitMart',
    'Bitrue', 'BingX', 'MEXC', 'DigiFinex', 'SuperEx', 'CoinCola', 'Ourbit',
    'Toobit', 'BloFin', 'BDFI', 'BYDFi', 'CoinW', 'BTCC', 'WEEX', 'LBank',
    'GMGN', 'KCEX', 'Kraken'
])

COIN_NAMES = [
    "Zeebu", "Fasttoken", "LayerZero", "IPVERSE", "Zignaly", "VeThor Token",
    "Orbler", "Boba Network", "CyberBots AI", "Helium Mobile", "Nosana",
    "Hivemapper", "World Mobile Token", "Shadow Token", "NYM", "Pocket Network",
    "CUDOS", "OctaSpace", "Coinweb", "Gaimin", "Aleph.im", "IAGON",
    "KYVE Network", "XRADERS", "Delysium", "Ozone Chain", "Oraichain",
    "Artificial Liquid Intelligence", "Forta", "PlatON", "Agoras: Currency of Tau",
    "Victoria VR", "Dimitra", "Moca Coin", "dKargo", "Commune AI",
    "Hacken Token", "Numbers Protocol", "Sentinel Protocol", "UXLINK",
    "Data Ownership Protocol", "Avive World", "Aurora", "NuNet", "iMe Lab",
    "Cere Network", "NeyroAI", "GT Protocol", "FROKAI", "HyperGPT", "PARSIQ",
    "Vectorspace AI", "Degen", "Koinos", "Synesis One", "Lumerin", "QnA3.AI",
    "Xelis", "DDMTOWN", "DeepBrain Chain", "Nuco.cloud", "Waves Enterprise",
    "Eclipse", "GamerCoin", "Optimus AI", "Ta-da", "TRVL", "Big Data Protocol",
    "Bad Idea AI", "Phantasma", "bitsCrunch", "PIBBLE", "Robonomics.network",
    "Swash", "Lambda", "MATH", "SubQuery Network", "Lithium", "Lossless",
    "Bridge Oracle", "Avail", "Mande Network", "Crypto-AI-Robo.com", "Metahero",
    "Netvrk", "Smart Layer Network", "Effect AI", "Chirpley", "Ispolink",
    "Edge Matrix Computing", "Dock", "PureFi Protocol", "GNY", "DxChain Token", # Bu yerda vergul qo'shildi
    "B-cube.ai", "DOJO Protocol", "Propy", "AXIS Token", "LBRY Credits",
    "ClinTex CTi", "GoCrypto Token", "Three Protocol Token", "Idena",
    "Aimedis (new)", "UBIX.Network", "Cirus Foundation", "All In", "Neurashi",
    "Ojamu", "Raze Network", "Ubex", "Censored Ai", "Triall", "Pawtocol",
    "Covalent", "Connectome", "Altered State Token", "Autonolas", "Dtec",
    "Work X", "Grow Token", "Lavita AI", "Arbius", "EpiK Protocol", "Multiverse",
    "enqAI", "Humans.ai", "Y8U", "AI Network", "Jackal Protocol",
    "Morpheus Infrastructure Node", "Tradetomato", "BasedAI", "ISSP",
    "Aventis Metaverse", "NFMart", "The Winkyverse", "Next Gem AI", "Human",
    "AlphaScan AI", "Eternal AI", "DataHighway", "Balance AI", "A3S Protocol",
    "Ore", "inheritance Art", "Raven Protocol", "Swan Chain", "VEMP",
    "Flourishing AI", "Cloudbric", "Kin", "META PLUS TOKEN", "LUKSO",
    "Neuroni AI", "AI PIN", "Layer3", "Trace Network Labs", "GoSleep",
    "Chappyz", "Kambria", "Aion", "Acria.AI", "Ctomorrow Platform",
    "The Emerald Company", "Gomining", "EPIK Prime", "Myria", "AutoCrypto",
    "Cindicator", "Bottos", "Eurite", "Bloktopia", "Runesterminal",
    "RSIC•GENESIS•RUNE", "WELL3", "Alpine F1 Team", "Verida", "Galaxis",
    "Energi", "Build", "DecideAI", "5ire", "Slash Vision Labs", "Star Protocol"
]

VOLUME_THRESHOLD = 5000  # USD

# === SPLIT COINS INTO THREE ===

def split_coins():
    n = len(COIN_NAMES)
    c = n // 3
    return {
        "coingecko": COIN_NAMES[:c],
        "coincap": COIN_NAMES[c:2*c],
        "coinpaprika": COIN_NAMES[2*c:]
    }

# === FETCH FUNCTIONS ===

async def fetch_coingecko(session, coin_name):
    # Coingecko ID ba'zan nomidan farq qilishi mumkin. Agar API noto'g'ri ID berayotgan bo'lsa,
    # bu qismni to'g'irlash kerak bo'ladi. Hozircha mavjud usulni saqlab qolamiz.
    _id = coin_name.lower().replace(" ", "-").replace(".", "") # Ba'zi nomlarda nuqta bo'lishi mumkin
    url = f"https://api.coingecko.com/api/v3/coins/{_id}/tickers"
    try:
        async with session.get(url) as response: # aiohttp session dan to'g'ri foydalanish
            response.raise_for_status() # HTTP xatolarini tekshirish
            data = await response.json()
            prices = [t for t in data.get("tickers", []) if t['market']['name'] in ALLOWED_EXCHANGES]
            if not prices:
                return coin_name, None
            best = max(prices, key=lambda x: x['volume'])
            if best['converted_volume']['usd'] < VOLUME_THRESHOLD:
                return coin_name, None
            return coin_name, ("coingecko", float(best['converted_last']['usd']), float(best['converted_volume']['usd']))
    except aiohttp.ClientError as e: # aniqroq xatolarni ushlash
        print(f"Error fetching {coin_name} from CoinGecko: {e}")
        return coin_name, None
    except Exception as e: # boshqa kutilmagan xatolarni ushlash
        print(f"Unexpected error with CoinGecko for {coin_name}: {e}")
        return coin_name, None


async def fetch_coinpaprika(session, coin_name):
    _id = coin_name.lower().replace(" ", "-").replace(".", "") # Ba'zi nomlarda nuqta bo'lishi mumkin
    url = f"https://api.coinpaprika.com/v1/tickers/{_id}"
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            # Coinpaprika API ba'zan "error" yoki "message" kalitlarini qaytarishi mumkin.
            # Agar data "id" kalitini o'z ichiga olmasa, bu coin topilmaganligini anglatadi.
            if "error" in data or "message" in data or "id" not in data:
                return coin_name, None

            markets = [m for m in data.get("markets", []) if m['exchange_name'] in ALLOWED_EXCHANGES]
            if not markets:
                return coin_name, None
            best = max(markets, key=lambda x: x['volume_usd'])
            if best['volume_usd'] < VOLUME_THRESHOLD:
                return coin_name, None
            return coin_name, ("coinpaprika", float(best['price']), float(best['volume_usd']))
    except aiohttp.ClientError as e:
        print(f"Error fetching {coin_name} from Coinpaprika: {e}")
        return coin_name, None
    except Exception as e:
        print(f"Unexpected error with Coinpaprika for {coin_name}: {e}")
        return coin_name, None

async def fetch_coincap(session, coin_name):
    # Coincap API da ba'zi tokenlar uchun to'liq nom emas, balki qisqartma ishlatilishi mumkin.
    # Bu yerda `baseSymbol` uchun nomni to'g'ri shakllantirish muhim.
    # Agar API noto'g'ri javob qaytarsa, bu qismni optimallashtirish kerak.
    # Misol uchun, "LayerZero" uchun "ZRO" ishlatilishi mumkin.
    base = coin_name.upper().replace(" ", "%20") # Probelni URL uchun kodlash
    url = f"https://api.coincap.io/v2/markets?baseSymbol={base}"
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            # Coincap API da 'exchangeId' kaliti kichik harflarda bo'lishi mumkin
            # va 'exchangeId' emas, balki 'exchangeId' deb kelishi mumkin.
            # Shuningdek, 'data' bo'sh bo'lsa, hech qanday ma'lumot yo'qligini anglatadi.
            markets = [m for m in data.get("data", []) if m.get('exchangeId') and m['exchangeId'] in [e.lower() for e in ALLOWED_EXCHANGES]]
            if not markets:
                return coin_name, None
            
            # volumeUsd24Hr ba'zan None yoki bo'sh satr bo'lishi mumkin, shuning uchun floatga o'tkazishdan oldin tekshirish
            best = max(markets, key=lambda x: float(x.get('volumeUsd24Hr') or 0))
            
            if float(best.get('volumeUsd24Hr') or 0) < VOLUME_THRESHOLD:
                return coin_name, None
            
            # priceUsd ham mavjudligini tekshirish
            if not best.get('priceUsd'):
                return coin_name, None

            return coin_name, ("coincap", float(best['priceUsd']), float(best['volumeUsd24Hr']))
    except aiohttp.ClientError as e:
        print(f"Error fetching {coin_name} from CoinCap: {e}")
        return coin_name, None
    except Exception as e:
        print(f"Unexpected error with CoinCap for {coin_name}: {e}")
        return coin_name, None

# === GATHER DATA ===

async def gather_prices():
    groups = split_coins()
    prices = {}

    async with aiohttp.ClientSession() as s:
        tasks = []
        for src, coins in groups.items():
            if src == "coingecko":
                tasks.extend([fetch_coingecko(s, c) for c in coins]) # extend dan foydalanish
            elif src == "coincap":
                tasks.extend([fetch_coincap(s, c) for c in coins])
            else: # src == "coinpaprika"
                tasks.extend([fetch_coinpaprika(s, c) for c in coins])

        # asyncio.gather() kutish natijasida barcha vazifalar tugashini ta'minlaydi
        results = await asyncio.gather(*tasks, return_exceptions=True) # Xatolarni qaytarish uchun

        for result in results:
            if isinstance(result, Exception): # Agar vazifa xato qaytargan bo'lsa
                print(f"Task failed: {result}")
                continue # Keyingi natijaga o'tish

            coin, data = result
            if data:
                src, price, vol = data
                prices.setdefault(coin.upper(), {})[src] = (price, vol)

    return prices

# === DETECT ARBITRAGE ===

def detect_arbitrage(prices):
    ops = []
    for coin, data in prices.items():
        valid = {s: p for s, (p, v) in data.items()}
        if len(valid) < 2:
            continue
        min_src = min(valid, key=valid.get)
        max_src = max(valid, key=valid.get)
        min_p, max_p = valid[min_src], valid[max_src]
        profit = (max_p - min_p) / min_p * 100
        if 3 <= profit <= 15:
            ops.append({
                "coin": coin,
                "buy": min_src,
                "bprice": min_p,
                "sell": max_src,
                "sprice": max_p,
                "profit": round(profit, 2)
            })
    return ops

# === ALERT ===

async def send_alert(ctx, ops):
    for o in ops:
        msg = (
            f"🚀 <b>Arbitrage Alert!</b>\n"
            f"🪙 {o['coin']}: Buy @ {o['buy']} (${o['bprice']:.4f}), "
            f"Sell @ {o['sell']} (${o['sprice']:.4f})\n"
            f"💸 Profit: <b>{o['profit']}%</b>\n"
            f"⏱ {datetime.utcnow().strftime('%H:%M:%S UTC')}"
        )
        # ADMIN_TELEGRAM_ID ni for-loop ichida iteratsiya qilish
        for admin_id in ADMIN_TELEGRAM_ID:
            await ctx.bot.send_message(chat_id=admin_id, text=msg, parse_mode='HTML')

# === SCHEDULED TASK ===

async def check(ctx):
    print(f"Checking for arbitrage opportunities at {datetime.utcnow().strftime('%H:%M:%S UTC')}...")
    prices = await gather_prices()
    ops = detect_arbitrage(prices)
    if ops:
        await send_alert(ctx, ops)
    else:
        print("No arbitrage opportunities found.")

# === COMMANDS ===

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchini botning ishlashi haqida xabardor qilish
    if update.effective_chat.id in ADMIN_TELEGRAM_ID:
        await update.message.reply_text("🤖 Arbitrage Bot started! I will send alerts to you.")
        # check() funksiyasiga ContextTypes ni to'g'ri o'tkazish
        ctx.job_queue.run_repeating(check, interval=180, first=5, data=ctx)
    else:
        await update.message.reply_text("Siz botni ishga tushirish uchun ruxsatga ega emassiz.")


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Foydalanuvchi status so'raganda xabar berish
    await update.message.reply_text("👋 Hello! I'm currently monitoring for arbitrage opportunities. You will be a millionaire! 💸")

async def check_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Bu komanda faqat administratorlar uchun bo'lishi kerak.
    if update.effective_chat.id in ADMIN_TELEGRAM_ID:
        await update.message.reply_text("🔍 Manual check initiated...")
        await check(ctx) # check funksiyasini to'g'ridan-to'g'ri chaqirish
        await update.message.reply_text("Manual check completed.")
    else:
        await update.message.reply_text("Siz qo'lda tekshirishni ishga tushirish uchun ruxsatga ega emassiz.")


# === MAIN ===

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("check", check_cmd))
    print("🚀 Bot ready!")
    app.run_polling()

