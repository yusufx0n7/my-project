import asyncio
import aiohttp
import time
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging konfiguratsiyasi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# TOKEN va CHAT_ID ni qo'lda kiritamiz (o'zgartirilmasdan qoldirildi)
TELEGRAM_TOKEN = '7780864447:AAESpcIqmzNkN1CiyLM1WfRkzPMWPeq7dzU'
CHAT_IDS = ['7971306481', '6329050233']  # Chat ID lar ro'yxati

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

# Kuzatiladigan coinlar
COIN_IDS = [
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
    "GT Protocol", "FROKAI", "HyperGPT", "OORT", "PARSIQ", "Vectorspace AI", "Degen",
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
    "Aurora", "Ojamu", "Raze Network", "Ubex", "Censored Ai", "Triall", "Pawtocol",
    "Covalent", "Connectome", "Altered State Token", "Autonolas", "Dtec", "Work X",
    "Grow Token", "Lavita AI", "Arbius", "EpiK Protocol", "Multiverse", "enqAI",
    "Humans.ai", "Y8U", "AI Network", "Jackal Protocol", "Morpheus Infrastructure Node",
    "Tradetomato", "BasedAI", "ISSP", "Aventis Metaverse", "NFMart",
    "The Winkyverse", "Next Gem AI", "Human", "AlphaScan AI", "Eternal AI",
    "DataHighway", "Balance AI", "A3S Protocol", "Ore", "inheritance Art",
    "Raven Protocol", "Swan Chain (formerly FilSwan)", "VEMP", "Flourishing AI",
    "Cloudbric", "Kin", "META PLUS TOKEN", "LUKSO", "Neuroni AI", "AI PIN", "Layer3",
    "Trace Network Labs", "GoSleep", "Chappyz", "Kambria", "Aion", "Acria.AI",
    "Ctomorrow Platform", "The Emerald Company", "Gomining", "EPIK Prime", "Myria",
    "AutoCrypto", "Cindicator", "Bottos", "Eurite", "Bloktopia", "Runesterminal",
    "RSIC•GENESIS•RUNE", "WELL3", "Alpine F1 Team", "Verida", "Galaxis", "Energi",
    "Build", "DecideAI", "5ire", "Slash Vision Labs", "Star Protocol", "Fautor",
    "BIDZ Coin", "Port3 Network", "KITEAI", "Super Zero Protocol", "ChatAI Token",
    "Alltoscan", "Hathor", "Spacemesh", "Woonkly Power", "ANyONe Protocol", "Chromia",
    "Oasys", "Zano", "Concordium", "NuLink", "Wisdomise AI", "Synternet",
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
    "Zircuit", "OORT", "Sensay", "Brickken", "Laika AI", "SUPRA", "PUMLx",
    "Banana Gun", "ACENT", "Fame AI", "Gather", "BRC App", "Rowan Coin", "Tamkin",
    "XRP Healthcare", "Open Loot", "Tornado Cash", "peaq", "MVL", "Open Campus",
    "Simmi Token", "XION", "ORA", "Alkimi", "Gravity", "BugsCoin", "Fluence",
    "Magic Eden", "Movement", "DIMO", "Heurist AI", "OBORTECH", "KLEAR", "Neuton",
    "KIP Protocol", "Propchain", "Agents AI", "Ripple USD", "Kaspa", "Worldcoin",
    "Chromia", "Shieldeum", "AI Agent Layer", "Guru Network", "UnMarshal", "Vana",
    "Nirvana", "Skillful AI", "Bepro", "Solvex Network", "RWA Inc.", "CodeXchain",
    "Deeper Network", "RARI", "U2U Network", "Pax Dollar", "Peercoin",
    "Quantum Resistant Ledger", "Elastos", "StorX Network", "Helium IOT", "Sentinel",
    "Stratos", "Bitfinity Network", "Kroma", "Laïka", "Handshake", "Crust Network",
    "PAAL AI", "KARRAT", "KOLZ", "OctonetAI", "Edge", "GRIFFAIN", "Parex",
    "Circular Protocol", "ResearchCoin", "Hippocrat", "CryptoAutos", "Pepecoin",
    "Luckycoin", "SETAI", "Junkcoin", "Reploy", "FLock..io", "Network DSYNC",
    "Bio Protocol", "Mobius", "Mysterium", "Raiden Network Token", "YOM", "Odyssey",
    "SōzōAI", "aixbt by Virtuals", "Sonic (prev. FTM)", "CRT AI Network",
    "STORAGENT", "BoltAI", "Fuel Network", "Function X", "cheqd", "neur.sh",
    "Limitus", "ZayaAI", "sekoia by Virtuals", "Realis Worlds", "HTERM", "HashAI",
    "CGAI", "SUIRWA", "Nodecoin", "BIDP", "Envision", "Spore.fun", "GoatIndex.ai",
    "DigiHealth", "ULTIMA", "Act I : The AI Prophecy", "Energy Web Token",
    "Dragonchain", "Phicoin", "ai16z", "Plume", "HAT", "SONIC", "VirtualDaos",
    "Chintai", "DAR Open Network", "Venice Token", "Creo Engine", "Morpheus",
    "GoPlus Security", "yesnoerror", "CreatorBid", "Alchemist AI", "Symbol",
    "Etherland", "Hive Intelligence", "Network3", "LAK3", "NTMPI", "Onyxcoin",
    "Partisia Blockchain", "SUI Desci Agents", "Aventus", "Blocery", "Boson Protocol",
    "CENNZnet", "Unification", "SOLVE", "Bitswift", "Hyperblox", "Neblio",
    "Smart MFG", "BLOCKv", "Suku", "Analog", "DIAM", "Atomicals", "Camino Network",
    "Story", "Nexus", "Ancient8", "Coldstack", "ScPrime", "Etho Protocol", "Sallar",
    "Academic Labs", "Electroneum", "KAITO", "Groestlcoin", "FileStar", "Particl",
    "Micro GPT", "PSJGlobal", "StorageChain", "Agoric", "MyShell", "EPAY",
    "Open Custody Protocol", "Assist AI", "AIST", "Collaterize", "JobSeek AI",
    "SafeCircle", "SwarmNode.ai", "MAIAR", "ArtGee AI", "Immutable", "Kendo AI",
    "Helio", "AI Rig Complex", "Bifrost", "Skey Network", "Xterio", "Blombard",
    "OpenBlox", "Bubblemaps", "Roam", "HYPE3-cool", "SINGULAR", "Uquid Coin",
    "Nillion", "CrypTalk", "GINI", "Particle Network", "Nireafty", "Safe Road Club AI",
    "StraitsX USD", "XSGD", "XIDR", "Paraverse", "Walrus", "Flare AI", "Sender",
    "MiL.k", "Wayfinder", "WalletConnect", "Mind Network", "Talken", "ACENT",
    "Hyperlane", "Saakuru Protocol", "Balance", "Arkham", "Ankr", "Altlayer",
    "Royalty", "Mansory", "Arcana Network", "Sign", "Pundi X (New)", "AQA",
    "AGiXT", "Treasure", "Nuklai", "AirDAO", "Neutron", "NexusChain", "AVA AI",
    "VITE", "OKZOO", "Cratos", "Propbase", "Step App", "Obortech", "Carnomaly",
    "Cryptify AI", "Argocoin", "Frictionless", "Heima", "Space and Time", "GPUs",
    "Domin Network", "Jupiter", "SKYAI", "SIX", "UPCX", "BSquared Network", "RWAI",
    "REENTAL", "Okratech Token", "MuxyAI", "Neon EVM", "TRI SIGMA", "DuckChain",
    "Alaya Governance Token", "Mint Blockchain", "Privasea AI", "Keep Network",
    "Houdini Swap", "OpenServ", "Rivalz Network", "Keeta", "Reef", "SOON",
    "Quai Network", "RYO Coin", "Epic Chain", "SoSoValue", "AWE Network",
    "Project Rescue", "Jambo", "Sophon", "Patex", "Moonchain", "Orbiter Finance",
    "iAI Center", "Assisterr", "DELNORTE", "Inferium", "Shardeum", "LayerEdge",
    "DeBox", "Block Vault", "Subsquid", "Everscale", "BONDEX", "Neuron", "NERTA",
    "NFTAI", "Lagrange", "Infinaeon", "LENS", "AB", "TokenFi", "ssv.network",
    "solayer", "Zcash", "Fly.trade", "Mythos", "Ronin", "CUDIS", "PinLink",
    "DeepLink Protocol", "Skate", "AO", "ASTRA", "Token Metrics AI", "Reddio",
    "The Arena", "GAG Token", "ESX", "Matchain", "NAM", "DAOBase", "Tagger",
    "Bitcoin Silver AI", "REDBRICK", "BOTIFY", "SmartPractice", "Coral Protocol",
    "CLI.AI", "Newton Protocol", "Sahara AI", "Mango Network", "Distribute..ai",
    "Humanity Protocol", "DeLorean", "REVOX", "Paragon Tweaks", "Mealy",
    "Impossible Cloud Network", "WaterMinder", "Paynetic AI", "Velo", "LF",
    "VeBetterDAO", "MAP Protocol", "ChainGPT", "Cobak Token", "Blockprompt",
    "Sabai Protocol", "JuChain", "Pundi AI", "Infinity Ground", "Validity", "B3 (Base)"
]

# Global aiohttp sessionini saqlash uchun o'zgaruvchi
global_http_session: aiohttp.ClientSession = None

async def send_telegram_message(text: str):
    """Telegramga xabar yuborish"""
    if not global_http_session:
        logger.error("Aiohttp session hali yaratilmagan!")
        return

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

    for chat_id in CHAT_IDS:
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'} # HTML parse_mode qo'shildi
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

async def fetch_markets_data(session: aiohttp.ClientSession, coin_ids_batch: list[str]) -> list[dict]:
    """
    CoinGecko API dan 'coins/markets' endpointi orqali ma'lumotlarni olish.
    Bir so'rovda 100 tagacha koin.
    """
    ids_str = ",".join(coin_ids_batch)
    url = f'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}'
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 429: # Too Many Requests
                logger.warning(f"CoinGecko API limitiga yetildi (markets endpoint). Kutilmoqda...")
                retry_after = int(resp.headers.get('Retry-After', '60'))
                await asyncio.sleep(retry_after + 5)
                return await fetch_markets_data(session, coin_ids_batch) # Qayta urinish
            else:
                logger.warning(f"Markets API so'rovida xato ({ids_str}). Status: {resp.status}, Javob: {await resp.text()}")
                return []
    except asyncio.TimeoutError:
        logger.error(f"Markets API so'rovida timeout ({ids_str}).")
        return []
    except aiohttp.ClientError as e:
        logger.error(f"Markets API so'rovida tarmoq xatosi ({ids_str}): {e}")
        return []
    except Exception as e:
        logger.error(f"Markets API so'rovida kutilmagan xato ({ids_str}): {e}")
        return []

async def fetch_tickers_data(session: aiohttp.ClientSession, coin_id: str) -> dict:
    """
    CoinGecko API dan 'coins/{id}/tickers' endpointi orqali ma'lumotlarni olish.
    Arbitraj tahlili uchun zarur.
    """
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/tickers'
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 429:
                logger.warning(f"CoinGecko API limitiga yetildi (tickers endpoint - {coin_id}). Kutilmoqda...")
                retry_after = int(resp.headers.get('Retry-After', '60'))
                await asyncio.sleep(retry_after + 5)
                return await fetch_tickers_data(session, coin_id) # Qayta urinish
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
        logger.error(f"Tickers API so'rovida kutilmagan xato ({coin_id}): {e}")
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

        buy_volume = buy.get("converted_volume", {}).get("usd", 0)
        sell_volume = sell.get("converted_volume", {}).get("usd", 0)
        volume = min(buy_volume, sell_volume)

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

async def monitor_loop():
    """Asosiy monitoring tsikli - 'coins/markets' orqali umumiy ma'lumotlarni olish
    va keyin arbitraj imkoniyatini tekshirish.
    """
    batch_size = 100 # Bir so'rovda maksimal 100 ta koin
    while True:
        start_time = time.time()
        logger.info(f"🔍 Coinlarni skanerlash boshlandi ({time.strftime('%Y-%m-%d %H:%M:%S')})")

        # Koin ID'larini partiyalarga bo'lish
        coin_id_batches = [COIN_IDS[i:i + batch_size] for i in range(0, len(COIN_IDS), batch_size)]

        all_market_data = []
        for batch in coin_id_batches:
            market_data = await fetch_markets_data(global_http_session, batch)
            all_market_data.extend(market_data)
            # API cheklovlariga rioya qilish uchun har bir partiyadan keyin ozroq kutish
            # CoinGecko'ning 'markets' endpointi uchun 100 so'rov/minut limiti bor (Premiumda ko'proq).
            # Shuning uchun har partiyadan keyin 0.6 soniya kutish 100 ta so'rovni 60 soniyada bajarishga imkon beradi.
            await asyncio.sleep(0.6)

        logger.info(f"📊 {len(all_market_data)} ta koinning umumiy bozor ma'lumotlari olindi. Arbitraj tekshiruvi boshlanmoqda...")

        # Arbitraj tahlilini parallel bajarish (har bir koin uchun alohida 'tickers' so'rovi)
        # Buni ham partiyalarga bo'lib, API limitiga yetmaslik uchun ehtiyot bo'lish kerak.
        # Bu qism avvalgi botdan farqli o'laroq, endi faqat aniq arbitrajni tekshiradi.
        arbitrage_tasks = []
        for coin_id in COIN_IDS:
            arbitrage_tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id))

        # Har 100 ta arbitraj tekshiruvidan keyin kutish (agar kerak bo'lsa)
        # Bu yerda API limitiga yetmaslik uchun ehtiyot bo'lish kerak.
        # CoinGecko'ning 'tickers' endpointi uchun limit pastroq bo'lishi mumkin.
        # Agar 1000 ta koin bo'lsa, 100 tadan keyin kutish mantig'i:
        for i in range(0, len(arbitrage_tasks), batch_size):
            batch_tasks = arbitrage_tasks[i:i + batch_size]
            await asyncio.gather(*batch_tasks)
            if i + batch_size < len(arbitrage_tasks): # Oxirgi partiyadan keyin kutmaslik
                await asyncio.sleep(3) # Har 100 ta koin tekshiruvidan keyin kutish (moslashtiring)


        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"✅ Skanerlash va Arbitraj tekshiruvi tugadi. Davomiyligi: {duration:.2f} soniya.")
        
        # Qolgan vaqtni kutish (agar monitoring tez tugasa)
        remaining_time = 300 - duration # Jami 5 daqiqa (300 soniya)
        if remaining_time > 0:
            logger.info(f"⏳ Keyingi aylanishgacha {remaining_time:.0f} soniya kutish...")
            await asyncio.sleep(remaining_time)
        else:
            logger.warning(f"Monitoring aylanishi kutilganidan uzoqroq davom etdi ({duration:.2f}s). Keyingi aylanish darhol boshlanadi.")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start komandasi"""
    await update.message.reply_html("👋 Assalomu alaykum, Arbitraj Botiga xush kelibsiz!\n\nBot 24/7 rejimida ishlaydi va har 5 daqiqada arbitraj imkoniyatlarini tekshiradi.\n\n/check - Hozirgi arbitraj holatini tekshirish.")
    logger.info(f"'{update.effective_user.full_name}' (/start) buyrug'ini ishlatdi.")

async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check komandasi"""
    await update.message.reply_text("🔍 Tekshiruv boshlandi...")
    logger.info(f"'{update.effective_user.full_name}' (/check) buyrug'ini ishlatdi.")

    arbitrage_tasks = []
    batch_size = 100 # Cheklovni hisobga olish
    for i in range(0, len(COIN_IDS), batch_size):
        batch = COIN_IDS[i:i + batch_size]
        for coin_id in batch:
            arbitrage_tasks.append(analyze_arbitrage_opportunity(global_http_session, coin_id, check_mode=True))
        
        await asyncio.gather(*arbitrage_tasks[i:i + batch_size])
        if i + batch_size < len(COIN_IDS):
            await asyncio.sleep(3) # Har 100 ta koin tekshiruvidan keyin kutish

    await update.message.reply_text("✅ Tekshiruv yakunlandi!")
    logger.info("Tekshiruv yakunlandi.")

async def start_bot():
    """Botni ishga tushirish"""
    global global_http_session
    global_http_session = aiohttp.ClientSession()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("check", check_handler))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("Telegram bot ishga tushirildi.")

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
    logger.info(f"📋 Kuzatiladigan coinlar soni: {len(COIN_IDS)}")
    logger.info(f"🔄 Har 5 daqiqada avtomatik tekshiruv")
    logger.info(f"⏰ Boshlanish vaqti: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot o'chirildi (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Asyncio main loopda kutilmagan xato: {e}", exc_info=True)

