import asyncio
import aiohttp
import time
import logging
import json
import os
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
FEE_RATE = 0.002 # Komissiya hisobi

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
    "Rootstock Infrastructure Framework", "Optimism", "TRON", "GMT", "Moonriver",
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
    "Wormhole", "QuarkChain", "Hooked Protocol", "Saga", "Astar", "Ark", "Tensor",
    "Beam", "Kusama", "Omni Network", "aelf", "Holo", "WINkLink", "Tellor",
    "Bittensor", "StormX", "Status", "SafePal", "Siacoin", "Orchid", "Ontology Gas",
    "IoTeX", "Toncoin", "Fame AI", "Alephium", "Hasaki", "Tether Gold",
    "OriginTrail", "Casper", "Zeebu", "Fasttoken", "LayerZero", "IPVERSE",
    "Zignaly", "VeThor Token", "Orbler", "Boba Network", "CyberBots AI",
    "Helium Mobile", "Nosana", "Hivemapper", "World Mobile Token", "Shadow Token",
    "NYM", "Pocket Network", "CUDOS", "OctaSpace", "Coinweb", "Gaimin", "Aleph.im",
    "IAGON", "KYVE Network", "XRADERS", "Delysium", "Ozone Chain", "Oraichain",
    "Artificial Liquid Intelligence", "Forta", "PlatON", "Agoras: Currency of Tau",
    "Victoria VR", "Dimitra", "Moca Coin", "dKargo", "Commune AI", "Hacken Token",
    "Numbers Protocol", "Sentinel Protocol", "UXLINK", "Data Ownership Protocol",
    "Avive World", "Aurora", "NuNet", "iMe Lab", "Cere Network", "NeyroAI",
    "GT Protocol", "FROKAI", "HyperGPT", "PARSIQ", "Vectorspace AI", "Degen",
    "Koinos", "Synesis One", "Lumerin", "QnA3.AI", "Xelis", "DDMTOWN",
    "DeepBrain Chain", "Nuco.cloud", "Waves Enterprise", "Eclipse", "GamerCoin",
    "Optimus AI", "Ta-da", "TRVL", "Big Data Protocol", "Bad Idea AI", "Phantasma",
    "bitsCrunch", "PIBBLE", "Robonomics.network", "Swash", "Lambda", "MATH",
    "SubQuery Network", "Lithium", "Lossless", "Bridge Oracle", "Avail",
    "Mande Network", "Crypto-AI-Robo.com", "Metahero", "Netvrk", "Smart Layer Network",
    "Effect AI", "Chirpley", "Ispolink", "Edge Matrix Computing", "Dock",
    "PureFi Protocol", "GNY", "DxChain Token", "B-cube.ai", "DOJO Protocol", "Propy",
    "AXIS Token", "LBRY Credits", "ClinTex CTi", "GoCrypto Token", "Three Protocol Token",
    "Idena", "Aimedis (new)", "UBIX.Network", "Cirus Foundation", "All In", "Neurashi",
    "Ojamu", "Raze Network", "Ubex", "Censored Ai", "Triall", "Pawtocol",
    "Covalent", "Connectome", "Altered State Token", "Autonolas", "Dtec", "Work X",
    "Grow Token", "Lavita AI", "Arbius", "EpiK Protocol", "Multiverse", "enqAI",
    "Humans.ai", "Y8U", "AI Network", "Jackal Protocol", "Morpheus Infrastructure Node",
    "Tradetomato", "BasedAI", "ISSP", "Aventis Metaverse", "NFMart",
    "The Winkyverse", "Next Gem AI", "Human", "AlphaScan AI", "Eternal AI",
    "DataHighway", "Balance AI", "A3S Protocol", "Ore", "inheritance Art",
    "Raven Protocol", "Swan Chain", "VEMP", "Flourishing AI",
    "Cloudbric", "Kin", "META PLUS TOKEN", "LUKSO", "Neuroni AI", "AI PIN", "Layer3",
    "Trace Network Labs", "GoSleep", "Chappyz", "Kambria", "Aion", "Acria.AI",
    "Ctomorrow Platform", "The Emerald Company", "Gomining", "EPIK Prime", "Myria",
    "AutoCrypto", "Cindicator", "Bottos", "Eurite", "Bloktopia", "Runesterminal",
    "RSIC•GENESIS•RUNE", "WELL3", "Alpine F1 Team", "Verida", "Galaxis", "Energi",
    "Build", "DecideAI", "5ire", "Slash Vision Labs", "Star Protocol", "Fautor",
    "BIDZ Coin", "Port3 Network", "KITEAI", "Super Zero Protocol", "ChatAI Token",
    "Alltoscan", "Hathor", "Spacemesh", "Woonkly Power", "ANyONe Protocol", "Oasys",
    "Zano", "Concordium", "NuLink", "Wisdomise AI", "Synternet",
    "Q Protocol", "Self Chain", "XDAO", "EMAIL Token", "Hyve", "Kaarigar Connect",
    "ARCS", "GTC AI", "Taraxa", "Radiant", "Electra Protocol", "Nexa", "AgentLayer",
    "Epic Cash", "Saito", "Zenon", "Abelian", "Humanode", "MultiVAC",
    "Integritee Network", "MainnetZ", "Hide Coin", "Busy DAO", "WYZth", "CLV",
    "Karlsen", "Canxium", "Allbridge", "Ice Open Network", "KALICHAIN", "Witnet",
    "HIENS3", "Unique Network", "Calamari Network", "Ecoin official", "EthereumPoW",
    "/Reach", "Friend3", "ECOMI", "BORA", "MXC", "Adventure Gold", "Swarm",
    "LooksRare", "PolySwarm", "Virtual Versions", "SwftCoin", "Wirex Token",
    "Taki Games", "Polyhedra Network", "Dora Factory", "WiFi Map", "Sweat Economy",
    "Gala", "DappRadar", "EURC", "Iron Fish", "Scroll", "GEODNET", "POL (ex-MATIC)",
    "CARV", "Kylacoin", "Thought", "Naxion", "Andromeda", "LightLink", "Nordek",
    "SatoshiVM", "LiquidApps", "Holograph", "ZENQIRA", "AIA Chain", "Beldex",
    "Truflation", "Aki Network", "Aleo", "Cellframe", "Ariva", "FREEdom Coin",
    "Metaplex", "UMA", "Pirate Chain", "Dero", "HOPR", "ColossusXT", "Crypton",
    "Grass", "Bytecoin", "Vertcoin", "Cros", "MUA DAO", "FOGNET", "Fractal Network",
    "Wownero", "The Root Network", "XBorg", "Kaia", "NATIX Network", "Ctrl Wallet",
    "Assemble AI", "Telos", "KardiaChain", "Shiden Network", "xHashtag AI",
    "Lifeform Token", "EGO", "TARS AI", "Sui Name Service", "OMG Network", "Bit. Store",
    "Altura", "Cookie", "Æternity", "BytomDAO", "GoChain", "Batching. AI",
    "Plugin Decentralized Oracle", "Darwinia Network", "Revain", "myDID",
    "v. systems", "Vexanium", "Edgeware", "AME Chain", "Nexera", "Coreum",
    "Zircuit", "Sensay", "Brickken", "Laika AI", "SUPRA", "PUMLx",
    "Banana Gun", "Gather", "BRC App", "Rowan Coin", "Tamkin",
    "XRP Healthcare", "Open Loot", "Tornado Cash", "peaq", "MVL", "Open Campus",
    "Simmi Token", "XION", "ORA", "Alkimi", "Gravity", "BugsCoin", "Fluence",
    "Magic Eden", "Movement", "DIMO", "Heurist AI", "OBORTECH", "KLEAR", "Neuton",
    "KIP Protocol", "Propchain", "Ripple USD", "Kaspa", "Worldcoin",
    "Shieldeum", "AI Agent Layer", "Guru Network", "UnMarshal", "Nirvana", "Skillful AI",
    "Bepro", "Solvex Network", "RWA Inc.", "CodeXchain", "Deeper Network", "RARI",
    "U2U Network", "Pax Dollar", "Peercoin", "Quantum Resistant Ledger", "Elastos",
    "StorX Network", "Helium IOT", "Sentinel", "Stratos", "Bitfinity Network", "Kroma",
    "Laïka", "Handshake", "Crust Network", "PAAL AI", "KARRAT", "KOLZ", "OctonetAI",
    "Edge", "GRIFFAIN", "Parex", "Circular Protocol", "ResearchCoin", "Hippocrat",
    "CryptoAutos", "Pepecoin", "Luckycoin", "SETAI", "Junkcoin", "Reploy",
    "FLock..io", "Network DSYNC", "Bio Protocol", "Mobius", "Mysterium",
    "Raiden Network Token", "YOM", "Odyssey", "SōzōAI", "aixbt by Virtuals",
    "Sonic (prev. FTM)", "CRT AI Network", "STORAGENT", "BoltAI", "Fuel Network",
    "Function X", "cheqd", "neur.sh", "Limitus", "ZayaAI", "sekoia by Virtuals",
    "Realis Worlds", "HTERM", "HashAI", "CGAI", "SUIRWA", "Nodecoin", "BIDP",
    "Envision", "Spore.fun", "GoatIndex.ai", "DigiHealth", "ULTIMA",
    "Act I : The AI Prophecy", "Energy Web Token", "Dragonchain", "Phicoin",
    "ai16z", "Plume", "HAT", "SONIC", "VirtualDaos", "Chintai", "DAR Open Network",
    "Venice Token", "Creo Engine", "Morpheus", "GoPlus Security", "yesnoerror",
    "CreatorBid", "Alchemist AI", "Symbol", "Etherland", "Hive Intelligence",
    "Network3", "LAK3", "NTMPI", "Onyxcoin", "Partisia Blockchain", "SUI Desci Agents",
    "Aventus", "Blocery", "Boson Protocol", "CENNZnet", "Unification", "SOLVE",
    "Bitswift", "Hyperblox", "Neblio", "Smart MFG", "BLOCKv", "Suku", "Analog",
    "DIAM", "Atomicals", "Camino Network", "Story", "Nexus", "Ancient8",
    "Coldstack", "ScPrime", "Etho Protocol", "Sallar", "Academic Labs", "Electroneum",
    "KAITO", "Groestlcoin", "FileStar", "Particl", "Micro GPT", "PSJGlobal",
    "StorageChain", "Agoric", "MyShell", "EPAY", "Open Custody Protocol", "Assist AI",
    "AIST", "Collaterize", "JobSeek AI", "SafeCircle", "SwarmNode.ai", "MAIAR",
    "ArtGee AI", "Immutable", "Kendo AI", "Helio", "AI Rig Complex", "Bifrost",
    "Skey Network", "Xterio", "Blombard", "OpenBlox", "Bubblemaps", "Roam",
    "HYPE3-cool", "SINGULAR", "Uquid Coin", "Nillion", "CrypTalk", "GINI",
    "Particle Network", "Nireafty", "Safe Road Club AI", "StraitsX USD", "XSGD",
    "XIDR", "Paraverse", "Walrus", "Flare AI", "Sender", "MiL.k", "Wayfinder",
    "WalletConnect", "Mind Network", "Talken", "Hyperlane", "Saakuru Protocol",
    "Balance", "Arkham", "Ankr", "Altlayer", "Royalty", "Mansory", "Arcana Network",
    "Sign", "Pundi X (New)", "AQA", "AGiXT", "Treasure", "Nuklai", "AirDAO",
    "Neutron", "NexusChain", "AVA AI", "VITE", "OKZOO", "Cratos", "Propbase",
    "Step App", "Obortech", "Carnomaly", "Cryptify AI", "Argocoin", "Frictionless",
    "Heima", "Space and Time", "GPUs", "Domin Network", "Jupiter", "SKYAI", "SIX",
    "UPCX", "BSquared Network", "RWAI", "REENTAL", "Okratech Token", "MuxyAI",
    "Neon EVM", "TRI SIGMA", "DuckChain", "Alaya Governance Token", "Mint Blockchain",
    "Privasea AI", "Keep Network", "Houdini Swap", "OpenServ", "Rivalz Network",
    "Keeta", "Reef", "SOON", "Quai Network", "RYO Coin", "Epic Chain", "SoSoValue",
    "AWE Network", "Project Rescue", "Jambo", "Sophon", "Patex", "Moonchain",
    "Orbiter Finance", "iAI Center", "Assisterr", "DELNORTE", "Inferium",
    "Shardeum", "LayerEdge", "DeBox", "Block Vault", "Subsquid", "Everscale",
    "BONDEX", "Neuron", "NERTA", "NFTAI", "Lagrange", "Infinaeon", "LENS", "AB",
    "TokenFi", "ssv.network", "solayer", "Zcash", "Fly.trade", "Mythos", "Ronin",
    "CUDIS", "PinLink", "DeepLink Protocol", "Skate", "AO", "ASTRA",
    "Token Metrics AI", "Reddio", "The Arena", "GAG Token", "ESX", "Matchain",
    "NAM", "DAOBase", "Tagger", "Bitcoin Silver AI", "REDBRICK", "BOTIFY",
    "SmartPractice", "Coral Protocol", "CLI.AI", "Newton Protocol", "Sahara AI",
    "Mango Network", "Distribute..ai", "Humanity Protocol", "DeLorean", "REVOX",
    "Paragon Tweaks", "Mealy", "Impossible Cloud Network", "WaterMinder",
    "Paynetic AI", "Velo", "LF", "VeBetterDAO", "MAP Protocol", "ChainGPT",
    "Cobak Token", "Blockprompt", "Sabai Protocol", "JuChain", "Pundi AI",
    "Infinity Ground", "Validity", "B3 (Base)"
]


# Global o'zgaruvchilar
global_http_session: aiohttp.ClientSession = None
coin_name_to_id_map = {} # Koin nomlarini IDlariga xaritalash
EFFECTIVE_COIN_IDS = []  # Faqat IDsi topilgan koinlar
COIN_BATCHES = []        # Koinlarning bo'limlarga bo'lingan ro'yxati
current_batch_index = 0  # Hozirgi tekshirilayotgan bo'lim indeksi

COINS_LIST_FILE = 'coingecko_coins_list.json' # Koinlar ro'yxati saqlanadigan fayl

# Monitoring tsiklining davomiyligi (3 daqiqa = 180 soniya)
TOTAL_CYCLE_DURATION_SECONDS = 180

# Koinlarni bo'lish kerak bo'lgan jami bo'limlar soni
TOTAL_BATCHES = 3 # Sizning talabingiz bo'yicha

# CoinGecko bepul API uchun minimal so'rovlar orasidagi kutish
# 'tickers' endpointi uchun pastroq limitlar bo'lishi mumkin.
MIN_API_CALL_DELAY_PER_COIN = 3 # Har bir 'tickers' so'rovidan keyin 3 soniya kutish

# --- Yordamchi funksiyalar ---
async def send_telegram_message(text: str):
    """Telegramga xabar yuborish"""
    if not global_http_session:
        logger.error("Aiohttp session hali yaratilmagan!")
        return

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

    for chat_id in CHAT_IDS:
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
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
    Arbitraj tahlili uchun zarur. Kesh va API limitini hisobga oladi.
    """
    current_time = time.time()
    if not force_refresh and coin_id in COIN_DATA_CACHE and \
       (current_time - COIN_DATA_CACHE[coin_id]['timestamp'] < CACHE_EXPIRATION_SECONDS):
        logger.debug(f"Keshdan yuklanmoqda: {coin_id}")
        return COIN_DATA_CACHE[coin_id]['data']

    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/tickers'
    try:
        # Har bir API so'rovidan oldin kutish
        # Bu erda parallelizm boshqariladi. asyncio.gather ichida bir nechta so'rov chaqirilsa ham,
        # bu delay har bir so'rovdan keyin amal qiladi.
        await asyncio.sleep(MIN_API_CALL_DELAY_PER_COIN)

        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                COIN_DATA_CACHE[coin_id] = {'data': data, 'timestamp': current_time}
                return data
            elif resp.status == 429: # Too Many Requests
                logger.warning(f"CoinGecko API limitiga yetildi (tickers endpoint - {coin_id}). Kutilmoqda...")
                retry_after = int(resp.headers.get('Retry-After', '60'))
                await asyncio.sleep(retry_after + 5) # Qo'shimcha kutish
                return await fetch_tickers_data(session, coin_id, force_refresh=True) # Qayta urinish
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

        volume = min(buy_volume_usd, sell_volume_usd) # USD dagi hajmni solishtirish

        if volume < MIN_VOLUME:
            return

        quantity = INVEST_AMOUNT / buy_price
        gross = quantity * sell_price
        fee = quantity * (buy_price + sell_price) * FEE_RATE
        net = gross - INVEST_AMOUNT - fee
        roi = (net / INVEST_AMOUNT) * 100

        if roi >= MIN_PROFIT and not check_mode:
            message = (
                f"<b>🚨 Arbitraj Imkoniyati</b>\n"
                f"<b>Coin:</b> {coin_id}\n"
                f"<b>Hajm:</b> {volume:.0f} USDT\n"
                f"<b>Buy:</b> {buy_price:.4f} ({buy['market']['name']})\n"
                f"<b>Sell:</b> {sell_price:.4f} ({sell['market']['name']})\n"
                f"<b>Komissiya:</b> {fee:.2f} USD\n"
                f"<b>Foyda:</b> {net:.2f} USD\n"
                f"<b>ROI:</b> {roi:.2f}%"
            )
            await send_telegram_message(message)
            logger.info(f"Arbitraj imkoniyati topildi va xabar yuborildi: {coin_id}, ROI: {roi:.2f}%")

        elif check_mode and CHECKABLE_MIN <= roi < CHECKABLE_MAX:
            message = (
                f"<b>ℹ️ Tekshiruv:</b> {coin_id}\n"
                f"<b>Buy:</b> {buy_price:.4f} ({buy['market']['name']})\n"
                f"<b>Sell:</b> {sell_price:.4f} ({sell['market']['name']})\n"
                f"<b>ROI:</b> {roi:.2f}%"
            )
            await send_telegram_message(message)
            logger.info(f"Tekshiruv xabari yuborildi: {coin_id}, ROI: {roi:.2f}%")

    except Exception as e:
        logger.error(f"⚠️ Arbitraj tahlilida kutilmagan xato ({coin_id}): {e}", exc_info=True)


async def get_or_load_coin_list(session: aiohttp.ClientSession):
    """
    CoinGecko'dan koinlar ro'yxatini yuklaydi yoki fayldan o'qiydi.
    Faqat bir marta, bot ishga tushganda chaqirilishi kerak.
    """
    if os.path.exists(COINS_LIST_FILE):
        logger.info(f"'{COINS_LIST_FILE}' faylidan koinlar ro'yxati yuklanmoqda.")
        with open(COINS_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.info("CoinGecko API dan koinlar ro'yxati olinmoqda (birinchi marta).")
        url = "https://api.coingecko.com/api/v3/coins/list"
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    with open(COINS_LIST_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    logger.info(f"Koinlar ro'yxati '{COINS_LIST_FILE}' fayliga saqlandi.")
                    return data
                else:
                    logger.error(f"Coin list olishda xato. Status: {resp.status}, Javob: {await resp.text()}")
                    return []
        except Exception as e:
            logger.error(f"Coin list olishda kutilmagan xato: {e}")
            return []

async def init_coin_ids():
    """Bot ishga tushganda koin nomlarini IDlarga tarjima qilish"""
    global coin_name_to_id_map, EFFECTIVE_COIN_IDS

    full_coin_list = await get_or_load_coin_list(global_http_session)
    for coin_entry in full_coin_list:
        coin_name_to_id_map[coin_entry['name'].lower()] = coin_entry['id'] # Nomlarni kichik harflarga o'girish
        # Agar symbol orqali ham qidirmoqchi bo'lsangiz, bu yerga qo'shishingiz mumkin:
        if 'symbol' in coin_entry:
            coin_name_to_id_map[coin_entry['symbol'].lower()] = coin_entry['id']


    found_count = 0
    not_found_names = []
    # INITIAL_COIN_NAMES ro'yxatidan foydalanamiz
    for name in INITIAL_COIN_NAMES:
        coin_id = coin_name_to_id_map.get(name.lower()) # Qidiruvni kichik harflarda bajarish
        if coin_id:
            EFFECTIVE_COIN_IDS.append(coin_id)
            found_count += 1
        else:
            not_found_names.append(name)

    logger.info(f"Topilgan koin IDlari soni: {found_count} / {len(INITIAL_COIN_NAMES)}")
    if not_found_names:
        logger.warning(f"CoinGecko'da topilmagan koin nomlari: {', '.join(not_found_names[:10])}{'...' if len(not_found_names) > 10 else ''}")

def get_coin_batches(all_coin_ids: list, num_batches: int) -> list[list]:
    """
    Koin IDlarini belgilangan sonli bo'limlarga teng taqsimlaydi.
    """
    if not all_coin_ids or num_batches <= 0:
        return []

    total_coins = len(all_coin_ids)
    if total_coins == 0:
        return []

    avg_batch_size = total_coins // num_batches
    remaining_coins = total_coins % num_batches

    batches = []
    current_index = 0
    for i in range(num_batches):
        batch_size = avg_batch_size + (1 if i < remaining_coins else 0)
        batch = all_coin_ids[current_index : current_index + batch_size]
        batches.append(batch)
        current_index += batch_size
    return batches

async def monitor_loop():
    """
    Asosiy monitoring tsikli - koinlarni bo'linmalarga bo'lib, aylanma tartibda tekshirish.
    """
    global EFFECTIVE_COIN_IDS, current_batch_index, COIN_BATCHES

    # Koinlar ro'yxati yuklanmagan bo'lsa kutish
    while not EFFECTIVE_COIN_IDS:
        logger.info("Koinlar ro'yxati yuklanishini kutilmoqda...")
        await asyncio.sleep(5)
        if not EFFECTIVE_COIN_IDS: # Hali ham bo'sh bo'lsa, qayta urinish
            await init_coin_ids()


    # Koinlarni bo'limlarga bo'lib olamiz (faqat bir marta)
    if not COIN_BATCHES:
        COIN_BATCHES = get_coin_batches(EFFECTIVE_COIN_IDS, TOTAL_BATCHES)
        if not COIN_BATCHES:
            logger.error("Koin bo'limlari yaratilmadi. Tekshiruvni boshlash mumkin emas.")
            return

    while True:
        start_scan_time = time.time()
        logger.info(f"🔍 Coinlarni skanerlash boshlandi ({time.strftime('%Y-%m-%d %H:%M:%S')})")

        # Navbatdagi bo'limni tanlash
        if current_batch_index >= len(COIN_BATCHES):
            current_batch_index = 0 # Ro'yxat oxiriga yetganda boshiga qaytish

        current_batch_ids = COIN_BATCHES[current_batch_index]

        # Telegramga tekshirilayotgan diapazon haqida xabar berish
        # Indekslarni aniq hisoblash
        total_coins_before_batch = sum(len(batch) for i, batch in enumerate(COIN_BATCHES) if i < current_batch_index)

        start_idx_for_message = total_coins_before_batch + 1 if current_batch_ids else 0
        end_idx_for_message = total_coins_before_batch + len(current_batch_ids) if current_batch_ids else 0

        batch_info_message = (
            f"🔄 Bot bo'limni tekshirmoqda: "
            f"<b>{start_idx_for_message}</b> dan <b>{end_idx_for_message}</b> gacha "
            f"({len(current_batch_ids)} ta koin). "
            f"Jami koinlar: {len(EFFECTIVE_COIN_IDS)}."
        )
        await send_telegram_message(batch_info_message)
        logger.info(batch_info_message)

        tasks = []
        for coin_id in current_batch_ids:
            tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id))

        # Parallel tekshiruvlarni bajarish
        if tasks:
            await asyncio.gather(*tasks)

        end_scan_time = time.time()
        scan_duration = end_scan_time - start_scan_time
        logger.info(f"✅ Bu bo'limdagi {len(current_batch_ids)} ta koin tekshirildi. Davomiyligi: {scan_duration:.2f} soniya.")

        # Keyingi bo'limga o'tish
        current_batch_index += 1

        # Keyingi umumiy aylanishgacha qolgan vaqtni kutish
        # Agar bo'limni tekshirish 3 daqiqadan ko'proq vaqt olsa, darhol keyingi bo'limga o'tamiz
        remaining_time = TOTAL_CYCLE_DURATION_SECONDS - scan_duration
        if remaining_time > 0:
            logger.info(f"⏳ Keyingi skanerlash aylanishgacha {remaining_time:.0f} soniya kutish...")
            await asyncio.sleep(remaining_time)
        else:
            logger.warning(f"Monitoring aylanishi kutilganidan uzoqroq davom etdi ({scan_duration:.2f}s). Keyingi bo'lim darhol boshlanadi.")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    await update.message.reply_html("👋 Assalomu alaykum, Arbitraj Botiga xush kelibsiz!\n\nBot 24/7 rejimida ishlaydi va koinlarni bo'linmalarga bo'lib, arbitraj imkoniyatlarini tekshiradi.\n\n/check - Hozirgi arbitraj holatini tekshirish.")
    logger.info(f"'{update.effective_user.full_name}' (/start) buyrug'ini ishlatdi.")

async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check komandasi"""
    await update.message.reply_text("🔍 Tekshiruv boshlandi...")
    logger.info(f"'{update.effective_user.full_name}' (/check) buyrug'ini ishlatdi.")

    if not EFFECTIVE_COIN_IDS:
        await update.message.reply_text("Koinlar ro'yxati hali yuklanmadi yoki bo'sh. Bir ozdan so'ng qayta urinib ko'ring.")
        logger.warning("Check buyrug'i berilganda koinlar ro'yxati bo'sh.")
        return

    tasks = []
    # /check buyrug'i uchun qancha koinni tekshirishni cheklaymiz.
    # Bu faqat tezkor tekshiruv bo'lgani uchun barcha koinlarni tekshirish shart emas.
    # Misol: faqat dastlabki 50 ta koinni tekshirish.
    COINS_TO_CHECK_FOR_COMMAND = 50

    checked_count = 0
    for coin_id in EFFECTIVE_COIN_IDS:
        if checked_count >= COINS_TO_CHECK_FOR_COMMAND:
            break

        # `force_refresh=True` bilan API dan yangi ma'lumot olishga urinish
        tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id, check_mode=True))
        checked_count += 1

    if tasks:
        await asyncio.gather(*tasks)

    await update.message.reply_text("✅ Tekshiruv yakunlandi! Natijalar xabarlarda yuboriladi (agar topilsa).")
    logger.info("Tekshiruv yakunlandi.")

async def start_bot():
    """Botni ishga tushirish"""
    global global_http_session
    global_http_session = aiohttp.ClientSession()

    await init_coin_ids() # CoinGecko ID larini yuklash va moslashtirish

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("check", check_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("Telegram bot ishga tushirildi.")

    # monitor_loop ni alohida task qilib ishga tushiramiz
    asyncio.create_task(monitor_loop())

    try:
        await asyncio.Event().wait()
    finally:
        if global_http_session:
            await global_http_session.close()
            logger.info("Aiohttp session yopildi.")

async def main():
    """Asosiy funksiya: botni qayta-qayta ishga tushiradi"""
    while True:
        try:
            logger.info(f"\n🚀 Bot ishga tushirilmoqda ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            await start_bot()
        except Exception as e:
            logger.critical(f"❌ Botda halokatli xato yuz berdi va to'xtatildi: {e}", exc_info=True)
            await send_telegram_message(f"🆘 Bot to'xtatildi! Halokatli xato: {e}")
            logger.info("♻️ 30 soniyadan keyin qayta ishga tushirilmoqda...")
            await asyncio.sleep(30)

if __name__ == "__main__":
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
        logger.info("Bot o'chirildi (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Asyncio main loopda kutilmagan xato: {e}", exc_info=True)
