import asyncio
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU'
ADMIN_TELEGRAM_ID = (7971306481, 6329050233) # Sizning admin ID(lar)ingiz

ALLOWED_EXCHANGES = {
    'Binance', 'CoinEx', 'AscendEX', 'HTX', 'Bitget', 'Poloniex', 'BitMart',
    'Bitrue', 'BingX', 'MEXC', 'DigiFinex', 'SuperEx', 'CoinCola', 'Ourbit',
    'Toobit', 'BloFin', 'BDFI', 'BYDFi', 'CoinW', 'BTCC', 'WEEX', 'LBank',
    'GMGN', 'KCEX', 'Kraken'
}

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
    "Edge Matrix Computing", "Dock", "PureFi Protocol", "GNY", "DxChain Token",
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

VOLUME_THRESHOLD = 5000

def split_coins():
    # Coincap olib tashlanganligi sababli, tangalar endi 2 ta guruhga bo'linadi
    n = len(COIN_NAMES)
    c = n // 2 # Teng ikkiga bo'lish
    return {
        "coingecko": COIN_NAMES[:c],
        "coinpaprika": COIN_NAMES[c:]
    }

async def fetch_coingecko(session, coin_name):
    try:
        _id = coin_name.lower().replace(" ", "-").replace(".", "").replace(":", "").replace("'","").replace("(", "").replace(")", "").replace(",","")
        url = f"https://api.coingecko.com/api/v3/coins/{_id}/tickers"
        async with session.get(url) as response:
            data = await response.json()
            if not data or "tickers" not in data:
                return coin_name, None

            tickers = [t for t in data.get("tickers", []) if t['market']['name'] in ALLOWED_EXCHANGES]
            if not tickers:
                return coin_name, None
            best = max(tickers, key=lambda x: x['volume'])
            if best['converted_volume']['usd'] < VOLUME_THRESHOLD:
                return coin_name, None
            return coin_name, ("coingecko", float(best['converted_last']['usd']), float(best['converted_volume']['usd']))
    except Exception as e:
        print(f"Error fetching {coin_name} from CoinGecko: {e}")
        return coin_name, None

async def fetch_coinpaprika(session, coin_name):
    try:
        _id = coin_name.lower().replace(" ", "-").replace(".", "").replace(":", "").replace("'","").replace("(", "").replace(")", "").replace(",","")
        # Coinpaprika uchun ID formatini tekshirish kerak
        url = f"https://api.coinpaprika.com/v1/tickers/{_id}"
        async with session.get(url) as response:
            data = await response.json()
            if "error" in data or not data: # Coinpaprika ba'zan xato obyektini qaytaradi
                return coin_name, None

            markets = [m for m in data.get("markets", []) if m['exchange_name'] in ALLOWED_EXCHANGES]
            if not markets:
                return coin_name, None
            best = max(markets, key=lambda x: x['volume_usd'])
            if best['volume_usd'] < VOLUME_THRESHOLD:
                return coin_name, None
            return coin_name, ("coinpaprika", float(best['price']), float(best['volume_usd']))
    except Exception as e:
        print(f"Error fetching {coin_name} from Coinpaprika: {e}")
        return coin_name, None

# Coincap endi yo'q
# async def fetch_coincap(session, coin_name):
#     try:
#         base = coin_name.upper().replace(" ", "%20")
#         url = f"https://api.coincap.io/v2/markets?baseSymbol={base}"
#         async with session.get(url) as response:
#             data = await response.json()
#             markets = [m for m in data.get("data", []) if m.get('exchangeId') and m['exchangeId'].lower() in [e.lower() for e in ALLOWED_EXCHANGES]]
#             if not markets:
#                 return coin_name, None
#             best = max(markets, key=lambda x: float(x.get('volumeUsd24Hr') or 0))
#             if float(best.get('volumeUsd24Hr') or 0) < VOLUME_THRESHOLD:
#                 return coin_name, None
#             return coin_name, ("coincap", float(best['priceUsd']), float(best['volumeUsd24Hr']))
#     except Exception as e:
#         print(f"Error fetching {coin_name} from CoinCap: {e}")
#         return coin_name, None

async def gather_prices():
    groups = split_coins()
    prices = {}
    async with aiohttp.ClientSession() as s:
        tasks = []
        for src, coins in groups.items():
            if src == "coingecko":
                tasks.extend([fetch_coingecko(s, c) for c in coins])
            elif src == "coinpaprika": # Faqat coinpaprika qoldi
                tasks.extend([fetch_coinpaprika(s, c) for c in coins])
        results = await asyncio.gather(*tasks)
        for result in results:
            coin, data = result
            if data:
                src, price, vol = data
                prices.setdefault(coin.upper(), {})[src] = (price, vol)
    return prices

def detect_arbitrage(prices):
    ops = []
    for coin, data in prices.items():
        valid = {s: p for s, (p, v) in data.items()}
        if len(valid) < 2: # Endi faqat 2 ta manba bor, shuning uchun hali ham kamida 2 ta bo'lishi kerak
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

async def send_alert(ctx, ops):
    for o in ops:
        msg = (
            f"🚀 <b>Arbitraj Ogohlantirishi!</b>\n"
            f"🪙 {o['coin']}: {o['buy']} dan sotib oling (${o['bprice']:.4f}), "
            f"{o['sell']} da soting (${o['sprice']:.4f})\n"
            f"💸 Foyda: <b>{o['profit']}%</b>\n"
            f"⏱ {datetime.utcnow().strftime('%H:%M:%S UTC')}"
        )
        for admin_id in ADMIN_TELEGRAM_ID:
            await ctx.bot.send_message(chat_id=admin_id, text=msg, parse_mode='HTML')

async def check_arbitrage(context: ContextTypes.DEFAULT_TYPE):
    print(f"Arbitraj {datetime.utcnow()} da tekshirilmoqda")
    prices = await gather_prices()
    ops = detect_arbitrage(prices)
    if ops:
        await send_alert(context, ops)
    else:
        print("Arbitraj imkoniyatlari topilmadi")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in ADMIN_TELEGRAM_ID:
        await update.message.reply_text("🤖 Arbitraj Boti ishga tushirildi! Har 3 daqiqada tekshiriladi.")
        context.job_queue.run_repeating(check_arbitrage, interval=180, first=5)
    else:
        await update.message.reply_text("⚠️ Sizda bu botni ishga tushirishga ruxsat yo'q!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot ishlamoqda va arbitraj imkoniyatlarini kuzatmoqda")

async def manual_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in ADMIN_TELEGRAM_ID:
        await update.message.reply_text("🔍 Qo'lda tekshirish boshlandi...")
        await check_arbitrage(context)
        await update.message.reply_text("✅ Qo'lda tekshirish yakunlandi")
    else:
        await update.message.reply_text("⚠️ Sizda qo'lda tekshirishni bajarishga ruxsat yo'q!")

if __name__ == '__main__':
    print("Bot ishga tushirilmoqda...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("check", manual_check))
    print("🚀 Bot tayyor va ishlamoqda!")
    app.run_polling()
