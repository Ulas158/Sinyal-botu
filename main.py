import os
import time
import random
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from io import StringIO

# ─────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID          = os.environ.get("CHAT_ID", "7116490869")
GITHUB_USER      = os.environ.get("GITHUB_USER", "Ulas158")
MAX_BARS         = 2
RSI_MAX          = 40.0
NW_ZONE          = 0.10
RETRY            = 3
BEKLEME_MIN      = 3.0
BEKLEME_MAX      = 6.0
BIST_HACIM_MIN   = 20_000_000
ABD_HACIM_MIN    = 10_000_000
KRIPTO_HACIM_MIN = 10_000_000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
    }

# ─────────────────────────────────────────────
# BIST — GitHub bist.txt
# ─────────────────────────────────────────────
BIST_YEDEK = [
    "AEFES","AGESA","AGHOL","AHGAZ","AKENR","AKBNK","AKFEN","AKGRT","AKSA","AKSEN",
    "ALARK","ALBRK","ALGYO","ALKIM","ALTNY","ANACM","ANELE","ANHYT","ANSGR","ARCLK",
    "ARSAN","ASELS","ASTOR","AYEN","AYGAZ","BAGFS","BALSU","BERA","BIOEN","BIZIM",
    "BJKAS","BNTAS","BOSSA","BRISA","BRKSN","BRSAN","BSOKE","BTCIM","BUCIM","BURCE",
    "BURVA","BRYAT","CANTE","CCOLA","CELHA","CEMAS","CEMTS","CIMSA","CLEBI","COKAS",
    "CRFSA","CUSAN","CVKMD","CWENE","DAGI","DAPGM","DARDL","DENGE","DESA","DEVA",
    "DITAS","DMSAS","DOAS","DOBUR","DOGUB","DOHOL","DOKTA","DSTKF","DYOBY","DZGYO",
    "ECILC","ECZYT","EDIP","EFOR","EGEEN","EGEPO","EGGUB","EGPRO","EKGYO","ENJSA",
    "ENKAI","ENERY","EPLAS","ERBOS","EREGL","ERSU","ESCAR","ESEN","ETILR","EUHOL",
    "EUPWR","EUREN","EUYO","FADE","FENER","FONET","FRIGO","FROTO","GARAN","GARFA",
    "GEDZA","GENIL","GEREL","GESAN","GLYHO","GLRMK","GMTAS","GOODY","GOZDE","GRSEL",
    "GRTHO","GSDHO","GSRAY","GUBRF","GWIND","HALKB","HATEK","HEDEF","HEKTS","HLGYO",
    "HOROZ","HUBVC","HUNER","HURGZ","ICBCT","INDES","INVEO","IPEKE","ISATR","ISBIR",
    "ISFIN","ISGYO","ISKPL","ISCTR","ISMEN","ISYAT","ITTFK","IZFAS","IZMDC","IZENR",
    "JANTS","KAPLM","KARTN","KARSN","KATMR","KAYSE","KCHOL","KENT","KERVT","KGYO",
    "KLGYO","KLKIM","KLRHO","KMPUR","KOCMT","KONYA","KONTR","KOPOL","KOZAL","KRDMD",
    "KRTEK","KTLEV","KUYAS","KUTPO","LIDER","LOGO","MAALT","MAGEN","MARTI","MAVI",
    "MAZGL","MEDTR","MEGAP","MERCN","MERIT","MERKO","METRO","MGROS","MIATK","MIPAZ",
    "MNDRS","MOBTL","MOGAN","MPARK","MSGYO","MTRKS","NATEN","NETAS","NIBAS","NTTUR",
    "NUHCM","OBASE","OBAMS","ODAS","ONCSM","ORCAY","ORGE","OSMEN","OSTIM","OTKAR",
    "OTTO","OYAKC","OYAYO","OYLUM","OZGYO","OZKGY","PAGYO","PAHOL","PAMEL","PAPIL",
    "PARSN","PASEU","PATEK","PEGYO","PEKMT","PENGD","PENTA","PETKM","PETUN","PGSUS",
    "PINSU","PKART","PLTUR","POLHO","PRZMA","PSGYO","PTOFS","QUAGR","RALYH","RAYSG",
    "REEDR","RNPOL","RODRG","ROYAL","RUBNS","RYGYO","SAFKR","SAHOL","SANEL","SANFM",
    "SANKO","SARKY","SASA","SAYAS","SEGYO","SEKUR","SELEC","SELGD","SELVA","SILVR",
    "SISE","SKBNK","SNGYO","SNPAM","SODSN","SOKM","SSTEK","SUWEN","TABGD","TATGD",
    "TATEN","TAVHL","TBORG","TCELL","TEKTU","TERA","TGSAS","THYAO","TKFEN","TKNSA",
    "TLMAN","TMPOL","TOASO","TRALT","TRCAS","TRENJ","TRMET","TRILC","TSGYO","TSKB",
    "TTKOM","TTRAK","TUCLK","TUKAS","TUPRS","TUREX","TURSG","UFUK","ULUUN","UMPAS",
    "ULKER","UNLU","USAK","VAKBN","VANGD","VBTYZ","VERUS","VESTL","VKFYO","VKGYO",
    "YAPRK","YATAS","YEOTK","YESIL","YGYO","YKBNK","YUNSA","YYAPI","ZEDUR","ZOREN",
]

def bist_listesi_cek():
    try:
        print("GitHub'dan bist.txt çekiliyor...")
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/bist.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            semboller = [
                line.strip().upper() + ".IS"
                for line in r.text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            semboller = list(dict.fromkeys(semboller))
            if len(semboller) >= 50:
                print(f"BIST: {len(semboller)} hisse")
                return semboller
        raise Exception(f"HTTP {r.status_code}")
    except Exception as e:
        print(f"bist.txt hatası: {e} — yedek liste")
        return [s + ".IS" for s in BIST_YEDEK]

# ─────────────────────────────────────────────
# ABD — S&P500 + NYSE top 2000 + NASDAQ top 500
# ─────────────────────────────────────────────
def abd_listesi_cek():
    semboller = []

    # 1) S&P 500
    try:
        print("S&P 500 çekiliyor...")
        url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
        r = requests.get(url, headers=get_headers(), timeout=15)
        df = pd.read_csv(StringIO(r.text))
        sp500 = [s.replace(".", "-") for s in df["Symbol"].dropna().tolist()]
        semboller.extend(sp500)
        print(f"S&P 500: {len(sp500)} hisse")
    except Exception as e:
        print(f"S&P 500 hatası: {e}")

    # 2) NYSE top 2000
    try:
        print("NYSE çekiliyor...")
        url = "https://raw.githubusercontent.com/datasets/nyse-listings/master/data/nyse-listed.csv"
        r = requests.get(url, headers=get_headers(), timeout=15)
        df = pd.read_csv(StringIO(r.text))
        col = [c for c in df.columns if "symbol" in c.lower() or "ticker" in c.lower()]
        if col:
            nyse = df[col[0]].dropna().tolist()[:2000]
            nyse = [str(s).strip() for s in nyse if str(s).strip() and "." not in str(s) and "$" not in str(s)]
            semboller.extend(nyse)
            print(f"NYSE: {len(nyse)} hisse")
    except Exception as e:
        print(f"NYSE hatası: {e}")

    # 3) NASDAQ top 500
    try:
        print("NASDAQ top 500 çekiliyor...")
        url = "https://raw.githubusercontent.com/Ate329/top-us-stock-tickers/main/tickers/all.csv"
        r = requests.get(url, headers=get_headers(), timeout=15)
        df = pd.read_csv(StringIO(r.text))
        col = [c for c in df.columns if "symbol" in c.lower() or "ticker" in c.lower()]
        if col:
            nasdaq = df[col[0]].dropna().tolist()[:500]
            nasdaq = [str(s).strip() for s in nasdaq if str(s).strip()]
            semboller.extend(nasdaq)
            print(f"NASDAQ top 500: {len(nasdaq)} hisse")
    except Exception as e:
        print(f"NASDAQ hatası: {e}")

    semboller = list(dict.fromkeys([
        s for s in semboller
        if s and len(s) <= 6 and s.replace("-", "").isalpha()
    ]))
    print(f"ABD toplam: {len(semboller)} hisse")
    return semboller

# ─────────────────────────────────────────────
# KRİPTO — CoinGecko top 400
# ─────────────────────────────────────────────
KRIPTO_YEDEK = [
    "BTC-USD","ETH-USD","BNB-USD","XRP-USD","SOL-USD","ADA-USD","DOGE-USD",
    "TRX-USD","DOT-USD","MATIC-USD","LTC-USD","SHIB-USD","AVAX-USD","UNI-USD",
    "LINK-USD","ATOM-USD","XLM-USD","ETC-USD","BCH-USD","APT-USD","FIL-USD",
    "NEAR-USD","ICP-USD","VET-USD","HBAR-USD","QNT-USD","ALGO-USD","GRT-USD",
    "EGLD-USD","AAVE-USD","XMR-USD","EOS-USD","SAND-USD","MANA-USD","AXS-USD",
    "THETA-USD","FTM-USD","FLOW-USD","STX-USD","XTZ-USD","DASH-USD","COMP-USD",
    "YFI-USD","SNX-USD","SUSHI-USD","1INCH-USD","CAKE-USD","OMG-USD","LRC-USD",
    "RUNE-USD","DYDX-USD","IMX-USD","GALA-USD","LDO-USD","APE-USD","OP-USD",
    "ARB-USD","SUI-USD","SEI-USD","TIA-USD","PYTH-USD","WIF-USD","BONK-USD",
    "PEPE-USD","FLOKI-USD","ORDI-USD","LUNC-USD","RAY-USD","INJ-USD","FET-USD",
    "RNDR-USD","OCEAN-USD","WLD-USD","JASMY-USD","ROSE-USD","MASK-USD",
]

def kripto_listesi_cek():
    try:
        print("GitHub'dan kripto.txt çekiliyor...")
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/kripto.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            semboller = [
                line.strip().upper() + "-USD"
                for line in r.text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            semboller = list(dict.fromkeys(semboller))
            if len(semboller) >= 50:
                print(f"Kripto: {len(semboller)} coin")
                return semboller
        raise Exception(f"HTTP {r.status_code}")
    except Exception as e:
        print(f"kripto.txt hatası: {e} — yedek liste")
        return KRIPTO_YEDEK

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram hatası: {e}")

# ─────────────────────────────────────────────
# YAHOO FİNANCE VERİ ÇEK
# ─────────────────────────────────────────────
def yahoo_veri_cek(ticker, deneme=0):
    try:
        session = requests.Session()
        session.headers.update(get_headers())
        try:
            session.get("https://fc.yahoo.com", timeout=5)
        except:
            pass
        try:
            crumb = session.get(
                "https://query1.finance.yahoo.com/v1/test/getcrumb",
                timeout=5
            ).text
        except:
            crumb = ""

        end   = int(time.time())
        start = end - 60 * 24 * 3600

        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={start}&period2={end}&interval=1h&crumb={crumb}"
        )
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        data  = r.json()
        chart = data.get("chart", {}).get("result", [])
        if not chart:
            return None

        timestamps = chart[0].get("timestamp", [])
        ohlcv      = chart[0]["indicators"]["quote"][0]

        df = pd.DataFrame({
            "Open":   ohlcv.get("open", []),
            "High":   ohlcv.get("high", []),
            "Low":    ohlcv.get("low", []),
            "Close":  ohlcv.get("close", []),
            "Volume": ohlcv.get("volume", []),
        }, index=pd.to_datetime(timestamps, unit="s", utc=True))

        df = df.dropna()
        if len(df) < 50:
            return None

        df = df.resample("4h").agg({
            "Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"
        }).dropna()

        if len(df) < 50:
            return None

        return df

    except Exception as e:
        if deneme < RETRY:
            time.sleep(3 * (deneme + 1))
            return yahoo_veri_cek(ticker, deneme + 1)
        return None

# ─────────────────────────────────────────────
# HACİM FİLTRESİ
# ─────────────────────────────────────────────
def hacim_gecti(ticker, df):
    try:
        son3gun   = df.tail(18)
        ort_hacim = son3gun["Volume"].mean()
        if ticker.endswith(".IS"):
            return ort_hacim >= BIST_HACIM_MIN
        elif ticker.endswith("-USD"):
            return ort_hacim >= KRIPTO_HACIM_MIN
        else:
            return ort_hacim >= ABD_HACIM_MIN
    except:
        return False

# ─────────────────────────────────────────────
# İNDİKATÖRLER
# ─────────────────────────────────────────────
def alma(src, length, offset=0.85, sigma=6.0):
    m = offset * (length - 1)
    s = length / sigma
    weights = np.array([np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(length)])
    weights /= weights.sum()
    result = np.full(len(src), np.nan)
    for i in range(length - 1, len(src)):
        result[i] = np.dot(src[i - length + 1:i + 1], weights[::-1])
    return result

def fisher_transform(high, low, length=9):
    hl2   = (high + low) / 2
    high_ = pd.Series(hl2).rolling(length).max().values
    low_  = pd.Series(hl2).rolling(length).min().values
    val   = np.zeros(len(hl2))
    fish1 = np.zeros(len(hl2))
    for i in range(1, len(hl2)):
        denom = high_[i] - low_[i]
        raw   = (
            0.66 * ((hl2[i] - low_[i]) / denom - 0.5) + 0.67 * val[i-1]
            if denom != 0 else 0.67 * val[i-1]
        )
        val[i]   = max(min(raw, 0.999), -0.999)
        fish1[i] = 0.5 * np.log((1 + val[i]) / (1 - val[i])) + 0.5 * fish1[i-1]
    fish2    = np.roll(fish1, 1)
    fish2[0] = np.nan
    return fish1, fish2

def rsi_hesapla(close, length=14):
    delta = pd.Series(close).diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_g = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_l = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs    = avg_g / avg_l
    return (100 - 100 / (1 + rs)).values

def nw_envelope(close, h=8.0, mult=3.0, n=200):
    if len(close) < n:
        n = len(close)
    src     = close[-n:]
    weights = np.array([np.exp(-(i**2) / (h * h * 2)) for i in range(n)])
    weights /= weights.sum()
    out = np.dot(src[::-1], weights)
    mae = np.mean(np.abs(src - out)) * mult
    return out, out - mae, out + mae

def crossover_bars_ago(a, b):
    for i in range(MAX_BARS + 1):
        idx = -1 - i
        if len(a) < abs(idx) + 1:
            return None
        if a[idx] > b[idx] and a[idx-1] <= b[idx-1]:
            return i
    return None

# ─────────────────────────────────────────────
# HİSSE TARA
# ─────────────────────────────────────────────
def hisse_tara(ticker):
    try:
        df = yahoo_veri_cek(ticker)
        if df is None:
            return False
        if not hacim_gecti(ticker, df):
            return False

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return False

        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False

        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None or rsi_vals[-1] > RSI_MAX:
            return False

        mid, lower, upper = nw_envelope(close, h=8.0, mult=3.0)
        zone = lower + (mid - lower) * NW_ZONE
        if close[-1] > zone or close[-1] < lower:
            return False

        return True

    except Exception as e:
        print(f"{ticker} hata: {e}")
        return False

# ─────────────────────────────────────────────
# ANA TARAMA
# ─────────────────────────────────────────────
def tara(hisse_listesi):
    print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Tarama başladı — {len(hisse_listesi)} sembol")
    bulunanlar_bist   = []
    bulunanlar_abd    = []
    bulunanlar_kripto = []

    for i, ticker in enumerate(hisse_listesi):
        print(f"  [{i+1}/{len(hisse_listesi)}] {ticker}", end=" ", flush=True)
        if hisse_tara(ticker):
            print("✓ SİNYAL")
            if ticker.endswith(".IS"):
                bulunanlar_bist.append(ticker.replace(".IS",""))
            elif ticker.endswith("-USD"):
                bulunanlar_kripto.append(ticker.replace("-USD",""))
            else:
                bulunanlar_abd.append(ticker)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    if bulunanlar_bist:
        mesaj = "🇹🇷 <b>BIST AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_bist:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if bulunanlar_abd:
        mesaj = "🇺🇸 <b>ABD AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_abd:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if bulunanlar_kripto:
        mesaj = "🪙 <b>Kripto AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_kripto:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if not any([bulunanlar_bist, bulunanlar_abd, bulunanlar_kripto]):
        print("\nSinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bist_listesi   = bist_listesi_cek()
    abd_listesi    = abd_listesi_cek()
    kripto_listesi = kripto_listesi_cek()
    tum_liste      = list(dict.fromkeys(bist_listesi + abd_listesi + kripto_listesi))

    toplam  = len(tum_liste)
    sure_dk = int(toplam * (BEKLEME_MIN + BEKLEME_MAX) / 2 / 60)

    telegram_gonder(
        f"🤖 <b>Kombine Sinyal Botu Başlatıldı!</b>\n\n"
        f"🇹🇷 BIST: {len(bist_listesi)} hisse\n"
        f"🇺🇸 ABD (S&P500+NYSE+NASDAQ): {len(abd_listesi)} hisse\n"
        f"🪙 Kripto (CoinGecko top 400): {len(kripto_listesi)} coin\n"
        f"🔢 Toplam: {toplam} sembol\n"
        f"⏱ Tarama süresi: ~{sure_dk} dakika\n\n"
        f"<b>Filtreler:</b>\n"
        f"• BIST Hacim ≥ 20M TL\n"
        f"• ABD Hacim ≥ 10M USD\n"
        f"• Kripto Hacim ≥ 10M USD\n"
        f"• Fisher crossover (2 mum, 0 altı)\n"
        f"• ALMA 4/9 crossover (2 mum)\n"
        f"• RSI ≤ 40\n"
        f"• NW Envelope alt %10\n\n"
        f"📅 Listeler her turda otomatik güncellenir"
    )

    while True:
        bist_listesi   = bist_listesi_cek()
        abd_listesi    = abd_listesi_cek()
        kripto_listesi = kripto_listesi_cek()
        tum_liste      = list(dict.fromkeys(bist_listesi + abd_listesi + kripto_listesi))
        tara(tum_liste)
        print("\nYeni tur başlıyor...\n")
