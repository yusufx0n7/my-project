import ccxt
import requests
import time
import threading

# === BU YERGA TOKEN VA ID NI KIRITING ===
TELEGRAM_TOKEN="7605062670:AAHLKWg-Zkow-j1y5mdWGli6MJafN3XRCxE"
CHAT_ID = "7971306481"

# === BOT SOZLAMALARI ===
MIN_PROFIT_PERCENT = 3.0
MIN_LIQUIDITY = 5000
CHESK_MODE_TIME = 300  # sekund (5 daqiqa)
PAIR_LIST = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "TON/USDT", "LINK/USDT", "DOT/USDT"]

CCXT_SUPPORTED_EXCHANGES = [
    "binance", "mexc", "coinex", "kraken", "huobi", "bitget",
    "poloniex", "bitmart", "bingx", "lbank", "digifinex"
]

COINGECKO_ONLY_EXCHANGES = [
    "superex", "toobit", "ascendex", "blofin", "bdfi", "bitrue", "bydfi",
    "coinw", "ourbit", "btcc", "weex", "gmgn", "kcex", "coincola"
]

EXCHANGES = CCXT_SUPPORTED_EXCHANGES + COINGECKO_ONLY_EXCHANGES

COINGECKO_IDS = {
    "a3s-protocol": "a3s-protocol",
    "abelian": "abelian",
    "acent": "acent",
    "alchemy-pay": "alchemy-pay",
    "acria-ai": "acria-ai",
    "act-i-the-ai-prophecy": "act-i-the-ai-prophecy",
    "cardano": "cardano",
    "adex": "adex",
    "adventure-gold": "adventure-gold",
    "aeternity": "aeternity",
    "aergo": "aergo",
    "agoras-currency-of-tau": "agoras-currency-of-tau",
    "agixt": "agixt",
    "aia-chain": "aia-chain",
    "ai-agent-layer": "ai-agent-layer",
    "ai-network": "ai-network",
    "ai-pin": "ai-pin", 
    "ai-rig-complex": "ai-rig-complex",
    "aimedis-new": "aimedis-new",
    "aixbt-by-virtuals": "aixbt-by-virtuals",
    "aki-network": "aki-network",
    "alaya-governance-token": "alaya-governance-token",
    "alchemist-ai": "alchemist-ai",
    "aleo": "aleo",
    "aleph-im": "aleph-im",
    "alephium": "alephium",
    "algorand": "algorand",
    "all-in": "all-in",
    "allbridge": "allbridge",
    "alltoscan": "alltoscan",
    "alpine-f1-team": "alpine-f1-team",
    "altlayer": "altlayer",
    "altura": "altura",
    "airdao": "airdao",
    "ame-chain": "ame-chain",
    "amp": "amp",
    "analog": "analog",
    "anchored-coins-aeur": "anchored-coins-aeur",
    "andromeda": "andromeda",
    "ankr": "ankr",
    "anyone-protocol": "anyone-protocol",
    "ao": "ao",
    "apecoin": "apecoin",
    "api3": "api3",
    "aptos": "aptos",
    "aqa": "aqa",
    "arbitrum": "arbitrum",
    "arbius": "arbius",
    "arbor": "arbor"
}

chesk_mode = False

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
    except requests.exceptions.RequestException as e:
        print(f"Telegramga xabar yuborishda xato: {e}")
        pass

def get_exchange(name):
    try:
        return getattr(ccxt, name)()
    except Exception as e:
        print(f"Birja ulanish xatosi ({name}): {e}")
        return None

def fetch_price_ccxt(exchange, pair):
    try:
        ticker = exchange.fetch_ticker(pair)
        return {
            "bid": ticker['bid'],
            "ask": ticker['ask'],
            "volume": ticker.get('baseVolume', 0)
        }
    except Exception as e:
        print(f"CCXT {exchange.id} {pair} xato: {e}")
        return None

def fetch_price_coingecko(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if coin_id in data and 'usd' in data[coin_id]:
            return {
                "bid": data[coin_id]['usd'],
                "ask": data[coin_id]['usd'],
                "volume": 999999999
            }
    except Exception as e:
        print(f"CoinGecko {coin_id} xato: {e}")
    return None

def fetch_price(exchange_name, symbol):
    coin_id = COINGECKO_IDS.get(symbol)
    if exchange_name in CCXT_SUPPORTED_EXCHANGES:
        exch = get_exchange(exchange_name)
        if exch:
            return fetch_price_ccxt(exch, symbol)
    elif exchange_name in COINGECKO_ONLY_EXCHANGES and coin_id:
        return fetch_price_coingecko(coin_id)
    return None

def check_arbitrage(pair):
    prices = []
    for name in EXCHANGES:
        price_info = fetch_price(name, pair)
        if price_info and price_info['bid'] and price_info['ask']:
            prices.append((name, price_info))

    if len(prices) < 2:
        return

    min_buy = min(prices, key=lambda x: x[1]['ask'])
    max_sell = max(prices, key=lambda x: x[1]['bid'])

    if min_buy[0] == max_sell[0] or min_buy[1]['ask'] == 0:
        return

    spread = max_sell[1]['bid'] - min_buy[1]['ask']
    profit_percent = (spread / min_buy[1]['ask']) * 100

    if profit_percent >= MIN_PROFIT_PERCENT and min_buy[1]['volume'] >= MIN_LIQUIDITY:
        msg = (f"💰 Arbitraj Topildi!\n"
               f"Coin: {pair}\n"
               f"⬇️ Sotib olish: {min_buy[0]} @ {min_buy[1]['ask']:.6f}\n"
               f"⬆️ Sotish: {max_sell[0]} @ {max_sell[1]['bid']:.6f}\n"
               f"📈 Foyda: {profit_percent:.2f}%")
        send_message(msg)
        print(f"ARBITRAJ: {pair} - {profit_percent:.2f}%")
    elif chesk_mode and profit_percent >= 1.0:
        msg = (f"🧐 Chesk imkoniyat: {pair}\n"
               f"⬇️ {min_buy[0]}: {min_buy[1]['ask']:.6f}\n"
               f"⬆️ {max_sell[0]}: {max_sell[1]['bid']:.6f}\n"
               f"📉 Foyda: {profit_percent:.2f}%")
        send_message(msg)
        print(f"CHESK: {pair} - {profit_percent:.2f}%")

def listen_bot():
    global chesk_mode
    offset = None
    chesk_start_time = 0
    print("Telegram komandalarini tinglash boshlandi...")
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        if offset:
            url += f"?offset={offset}"
        try:
            r = requests.get(url, timeout=10).json()
            for result in r.get('result', []):
                offset = result['update_id'] + 1
                message = result.get('message', {})
                text = message.get('text', '')
                chat_id_from_msg = message.get('chat', {}).get('id')
                if str(chat_id_from_msg) != CHAT_ID:
                    continue

                if text == "/start":
                    send_message("🟢 Bot ishga tushdi. Arbitraj tekshiruvi boshlandi.")
                elif text == "/chesk":
                    send_message("🧪 5 daqiqalik chesk rejimi ishga tushdi...")
                    chesk_mode = True
                    chesk_start_time = time.time()
                elif text:
                    print(f"Yangi xabar: {text}")
        except Exception as e:
            print(f"Telegram getUpdates xato: {e}")

        if chesk_mode and (time.time() - chesk_start_time > CHESK_MODE_TIME):
            chesk_mode = False
            send_message("✅ Chesk rejimi yakunlandi.")
        time.sleep(2)

def run_bot():
    print("Asosiy arbitraj tekshiruvi boshlandi...")
    check_interval = 300  # 5 daqiqa
    num_pairs = len(PAIR_LIST)
    delay_per_coin = check_interval / num_pairs if num_pairs > 0 else 1

    while True:
        cycle_start = time.time()
        print(f"Yangi davr boshlandi. {num_pairs} ta coin tekshirilmoqda...")

        for pair in PAIR_LIST:
            check_arbitrage(pair)
            time.sleep(delay_per_coin)

        elapsed = time.time() - cycle_start
        print(f"{num_pairs} ta coin tekshirildi. Davr davomiyligi: {elapsed:.1f} sekund.")

if __name__ == "__main__":
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        print("XATO: TELEGRAM_TOKEN va CHAT_ID to'g'ri emas.")
    else:
        telegram_thread = threading.Thread(target=listen_bot)
        bot_thread = threading.Thread(target=run_bot)

        telegram_thread.start()
        bot_thread.start()

        telegram_thread.join()
        bot_thread.join()
