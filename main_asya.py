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
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID         = os.environ.get("CHAT_ID", "7116490869")
MAX_BARS        = 2
RSI_MAX         = 40.0
NW_ZONE         = 0.10
RETRY           = 3
BEKLEME_MIN     = 3.0
BEKLEME_MAX     = 6.0
JAPONYA_HACIM   = 5_000_000   # 5M USD
HONGKONG_HACIM  = 5_000_000   # 5M USD
ALMANYA_HACIM   = 5_000_000   # ~5M EUR

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
# JAPONYA — JPX sitesinden otomatik çek
# ─────────────────────────────────────────────
def japonya_listesi_cek():
    # FinanceDataReader ile TSE listesi çek
    try:
        print("Japonya listesi çekiliyor (FinanceDataReader)...")
        import FinanceDataReader as fdr
        df = fdr.StockListing("TSE")
        semboller = [str(s).strip() + ".T" for s in df["Symbol"].dropna().tolist() if str(s).strip()]
        semboller = list(dict.fromkeys(semboller))
        if len(semboller) >= 100:
            print(f"Japonya (TSE): {len(semboller)} hisse")
            return semboller
        raise Exception(f"Yeterli sembol yok: {len(semboller)}")
    except Exception as e:
        print(f"FinanceDataReader TSE hatası: {e}")

    # Yedek: Wikipedia Nikkei 225
    try:
        print("Japonya yedek liste çekiliyor (Wikipedia)...")
        semboller = []
        url = "https://en.wikipedia.org/wiki/Nikkei_225"
        r = requests.get(url, headers=get_headers(), timeout=15)
        tablolar = pd.read_html(r.text)
        for tablo in tablolar:
            for col in tablo.columns:
                if "code" in str(col).lower() or "symbol" in str(col).lower():
                    kodlar = tablo[col].dropna().tolist()
                    for k in kodlar:
                        k = str(k).strip()
                        if k.isdigit() and len(k) == 4:
                            semboller.append(k + ".T")
        semboller = list(dict.fromkeys(semboller))
        if len(semboller) >= 50:
            print(f"Japonya (Wikipedia): {len(semboller)} hisse")
            return semboller
    except Exception as e:
        print(f"Wikipedia Nikkei hatası: {e}")

    # Son yedek: sabit Nikkei 225 listesi
    print("Japonya sabit liste kullanılıyor...")
    nikkei = [
        "7203","6758","9984","8306","6861","4063","6954","8035","7741","4502",
        "9432","9433","9984","8411","7267","7201","4519","6501","6752","6702",
        "4523","8058","8316","7751","6902","4568","8031","8053","4543","8802",
        "3382","6503","5401","9020","6301","8001","9022","4661","2914","8604",
        "6857","4901","1925","7011","8002","9021","6594","4755","2502","1928",
        "6762","8309","7013","4021","3407","4911","8830","1801","6674","6971",
        "6988","9613","4751","5108","8766","3659","7009","1802","4578","7733",
        "8801","6472","7832","4507","6326","6723","4188","5713","8750","5020",
        "9007","7270","6645","2269","8015","6273","8267","8355","3086","4452",
        "6841","9005","7011","2768","8591","5233","4704","6367","1721","8308",
        "4324","6506","9008","7735","6305","6645","2282","2002","7912","4612",
        "8253","7762","3289","2413","3101","3436","4042","6471","9009","5631",
        "7735","8601","6770","7911","2801","5332","4004","6361","5411","9062",
        "3861","7762","4183","6113","7205","5214","4151","7261","9101","9104",
        "6370","4005","7951","4183","6302","5703","7102","2871","4208","3105",
        "5706","4202","7313","3099","6724","2503","4922","4272","7205","6952",
        "2531","3861","5232","4118","7282","5301","6925","9064","6103","7269",
        "4997","5714","5726","6432","5110","7936","7906","5911","6815","7912",
        "6258","4185","5801","4042","5812","5541","5406","5423","5463","7202",
        "9101","5471","5463","5232","9104","5233","4042","5301","5411","9104",
        "5020","5714","5726","5801","5812","5911","6103","6113","6258","6302",
        "6361","6370","6432","6471","6506","6724","6815","6925","6952","7102",
        "7202","7205","7261","7269","7282","7313","7936","7906","9062","9064",
    ]
    return list(dict.fromkeys([k + ".T" for k in nikkei]))

# ─────────────────────────────────────────────
# HONG KONG — HKEX listesi
# ─────────────────────────────────────────────
def hongkong_listesi_cek():
    # FinanceDataReader ile HKEX listesi çek
    try:
        print("Hong Kong listesi çekiliyor (FinanceDataReader)...")
        import FinanceDataReader as fdr
        df = fdr.StockListing("HKEX")
        sonuc = []
        for s in df["Symbol"].dropna().tolist():
            s = str(s).strip().replace(".HK","")
            if s.isdigit():
                sonuc.append(s.zfill(4) + ".HK")
        sonuc = list(dict.fromkeys(sonuc))
        if len(sonuc) >= 50:
            print(f"Hong Kong (HKEX): {len(sonuc)} hisse")
            return sonuc
        raise Exception(f"Yeterli sembol yok: {len(sonuc)}")
    except Exception as e:
        print(f"FinanceDataReader HKEX hatası: {e}")

    # Yedek: Hang Seng bileşenleri
    print("Hong Kong sabit liste kullanılıyor...")
    hang_seng = [
        "0700","0941","1299","2318","0005","0388","1398","0939","3988","2628",
        "0883","0016","1113","0011","0012","0017","0002","0003","0006","0823",
        "1044","0688","0101","0027","0175","1928","0066","1038","0267","0762",
        "0857","0386","0241","0288","1177","2388","0291","1876","0669","0960",
        "1093","0868","2020","6862","0285","0960","1810","9988","3690","0020",
        "1024","0522","0992","2382","6618","0836","1997","1109","0868","2319",
        "0151","0656","0144","0135","0083","0659","0358","0019","1308","2777",
        "0570","0371","1918","0914","2007","0753","2313","0087","0138","0293",
        "0019","1357","0270","1171","0256","0257","1398","3328","6837","0386",
    ]
    return list(dict.fromkeys([k + ".HK" for k in hang_seng]))

# ─────────────────────────────────────────────
# ALMANYA — Frankfurt Borsası
# ─────────────────────────────────────────────
def almanya_listesi_cek():
    # FinanceDataReader ile Frankfurt listesi çek
    try:
        print("Almanya listesi çekiliyor (FinanceDataReader)...")
        import FinanceDataReader as fdr
        df = fdr.StockListing("XFRA")
        semboller = [str(s).strip() + ".DE" for s in df["Symbol"].dropna().tolist() if str(s).strip()]
        semboller = list(dict.fromkeys(semboller))
        if len(semboller) >= 20:
            print(f"Almanya (XFRA): {len(semboller)} hisse")
            return semboller
        raise Exception(f"Yeterli sembol yok: {len(semboller)}")
    except Exception as e:
        print(f"FinanceDataReader XFRA hatası: {e}")

    # Yedek: sabit DAX+MDAX+SDAX+TecDAX listesi
    print("Almanya sabit liste kullanılıyor...")
    almanya = [
        "SAP","AIR","ADS","ALV","MUV2","DTE","RWE","SIE","BMW","MBG",
        "DBK","DPW","HEI","VOW3","BAS","BAYN","ENR","FRE","HEN3","IFX",
        "MRK","MTX","PUM","QIA","RHM","SHL","SY1","VNA","ZAL","1COV",
        "AFX","AG1","AIXA","BOSS","CARL","COK","COP","EVD","FME","GFK",
        "HFG","HOT","JEN","KGX","LEG","LHA","LXS","MDO","NDX1","NEM",
        "O2D","PAH3","PBB","SDF","SFQ","SGL","SKB","SMHN","SZG","TLX",
        "TUI1","VBK","WAF","VOS","VIB3","UTDI","TPVG","TEG","TDT","SW",
        "SRT3","SLT","SIX2","SIS","RAA","RKET","PSM","PRG","NOEJ","NDA",
        "MVOB","MOR","MNX","MLP","KION","KD8","JUN3","IVU","ISRA","HHFA",
        "HDD","HAB","GXI","GWI","GBF","GAM","EVT","ERF","DHER","DEQ",
        "DBQ","DAR","CWC","CWB","CUE","CM","CIO","CEC","CBK","CAP",
        "BYW6","BWBK","BVB","BNR","BC8","BAF","AT1","ARL","APN","AOF",
        "AMO","ADV","ADL","ADJ","ADF","ADC","ACX","ACT",
    ]
    return list(dict.fromkeys([s + ".DE" for s in almanya]))

    # Yedek: DAX + MDAX + SDAX + TecDAX
    print("Almanya sabit liste kullanılıyor...")
    almanya = [
        "SAP","AIR","ADS","ALV","MUV2","DTE","RWE","SIE","BMW","MBG",
        "DBK","DPW","HEI","VOW3","BAS","BAYN","ENR","FRE","HEN3","IFX",
        "MRK","MTX","PUM","QIA","RHM","SHL","SY1","VNA","ZAL","1COV",
        "AFX","AG1","AIXA","BOSS","CARL","COK","COP","EVD","FME","GFK",
        "HFG","HOT","JEN","KGX","LEG","LHA","LXS","MDO","NDX1","NEM",
        "O2D","PAH3","PBB","SDAX","SDF","SFQ","SGL","SKB","SMHN","SZG",
        "TLX","TUI1","VBK","WIGE","WDI","WAF","VOS","VIB3","UTDI","TPVG",
        "TEG","TDT","SW","SRT3","SPCE","SLT","SIX2","SIS","SGRE","SCE",
        "RAA","RKET","PSM","PRG","NOEJ","NDA","MVOB","MOR","MNX","MLP",
        "KION","KD8","JUN3","IVU","ISRA","HHFA","HDD","HAB","GXI","GWI",
        "GBF","GAM","EVT","ERF","DHER","DEQ","DBQ","DAR","CWC","CWB",
        "CUE","CRON","CM","CIO","CEC","CBK","CAP","BYW6","BWBK","BVB",
        "BNR","BHRE","BFSA","BC8","BBB","BAF","AT1","ARL","APN","AOF",
        "AMZN","AMO","AIXA","ADV","ADL","ADJ","ADF","ADC","ACX","ACT",
    ]
    return list(dict.fromkeys([s + ".DE" for s in almanya]))

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
        if ticker.endswith(".T"):
            # Japonya: yen bazlı, 5M USD ≈ 750M yen
            return ort_hacim >= 750_000_000
        elif ticker.endswith(".HK"):
            return ort_hacim >= HONGKONG_HACIM
        elif ticker.endswith(".DE"):
            return ort_hacim >= ALMANYA_HACIM
        return False
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
    bulunanlar_jp = []
    bulunanlar_hk = []
    bulunanlar_de = []

    for i, ticker in enumerate(hisse_listesi):
        print(f"  [{i+1}/{len(hisse_listesi)}] {ticker}", end=" ", flush=True)
        if hisse_tara(ticker):
            print("✓ SİNYAL")
            if ticker.endswith(".T"):
                bulunanlar_jp.append(ticker)
            elif ticker.endswith(".HK"):
                bulunanlar_hk.append(ticker)
            elif ticker.endswith(".DE"):
                bulunanlar_de.append(ticker)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    if bulunanlar_jp:
        mesaj = "🇯🇵 <b>Japonya AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_jp:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if bulunanlar_hk:
        mesaj = "🇭🇰 <b>Hong Kong AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_hk:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if bulunanlar_de:
        mesaj = "🇩🇪 <b>Almanya AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_de:
            mesaj += f"  • {h}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW %10"
        telegram_gonder(mesaj)

    if not any([bulunanlar_jp, bulunanlar_hk, bulunanlar_de]):
        print("\nSinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    jp_listesi = japonya_listesi_cek()
    hk_listesi = hongkong_listesi_cek()
    de_listesi = almanya_listesi_cek()
    tum_liste  = list(dict.fromkeys(jp_listesi + hk_listesi + de_listesi))

    toplam  = len(tum_liste)
    sure_dk = int(toplam * (BEKLEME_MIN + BEKLEME_MAX) / 2 / 60)

    telegram_gonder(
        f"🤖 <b>Bot 3 — Asya/Avrupa Başlatıldı!</b>\n\n"
        f"🇯🇵 Japonya: {len(jp_listesi)} hisse\n"
        f"🇭🇰 Hong Kong: {len(hk_listesi)} hisse\n"
        f"🇩🇪 Almanya: {len(de_listesi)} hisse\n"
        f"🔢 Toplam: {toplam} sembol\n"
        f"⏱ Tarama süresi: ~{sure_dk} dakika\n\n"
        f"<b>Filtreler:</b>\n"
        f"• Japonya Hacim ≥ 750M JPY (~5M USD)\n"
        f"• Hong Kong Hacim ≥ 5M USD\n"
        f"• Almanya Hacim ≥ 5M EUR\n"
        f"• Fisher crossover (2 mum, 0 altı)\n"
        f"• ALMA 4/9 crossover (2 mum)\n"
        f"• RSI ≤ 40\n"
        f"• NW Envelope alt %10\n\n"
        f"📅 Liste her turda otomatik güncellenir"
    )

    while True:
        jp_listesi = japonya_listesi_cek()
        hk_listesi = hongkong_listesi_cek()
        de_listesi = almanya_listesi_cek()
        tum_liste  = list(dict.fromkeys(jp_listesi + hk_listesi + de_listesi))
        tara(tum_liste)
        print("\nYeni tur başlıyor...\n")
