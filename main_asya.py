import os
import time
import random
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from tvDatafeed import TvDatafeed, Interval

# ─────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID", "7116490869")
GITHUB_USER    = os.environ.get("GITHUB_USER", "Ulas158")
TV_USERNAME    = os.environ.get("TV_USERNAME", "")
TV_PASSWORD    = os.environ.get("TV_PASSWORD", "")
MAX_BARS       = 2
RSI_MAX        = 40.0
NW_ZONE        = 0.10
BEKLEME_MIN    = 0.5
BEKLEME_MAX    = 1.5
JAPONYA_HACIM  = 750_000_000
HONGKONG_HACIM = 5_000_000
ALMANYA_HACIM  = 5_000_000
N_BARS         = 500

# tvDatafeed bağlantısı
try:
    if TV_USERNAME and TV_PASSWORD:
        tv = TvDatafeed(TV_USERNAME, TV_PASSWORD)
        print("TradingView hesabıyla bağlandı ✓")
    else:
        tv = TvDatafeed()
        print("TradingView anonim bağlandı ✓")
except Exception as e:
    tv = TvDatafeed()

# ─────────────────────────────────────────────
# JAPONYA LİSTESİ
# ─────────────────────────────────────────────
JAPONYA_LISTE = [
    "1301","1332","1333","1605","1721","1801","1802","1803","1808","1812",
    "1925","1928","1963","2002","2269","2282","2413","2432","2501","2502",
    "2503","2531","2579","2768","2801","2802","2871","2914","3086","3099",
    "3197","3289","3382","3402","3405","3407","3436","3659","3861","3863",
    "3865","3866","3891","4004","4005","4021","4042","4043","4061","4063",
    "4183","4188","4202","4203","4204","4205","4208","4272","4307","4324",
    "4385","4452","4502","4503","4506","4507","4519","4523","4528","4543",
    "4568","4578","4631","4642","4661","4689","4704","4751","4755","4901",
    "4902","4911","5001","5002","5019","5020","5101","5108","5201","5202",
    "5214","5233","5301","5332","5333","5334","5401","5406","5411","5413",
    "5631","5706","5707","5711","5713","5714","5715","5801","5802","5803",
    "6301","6302","6305","6326","6361","6367","6471","6472","6473","6501",
    "6503","6504","6506","6645","6674","6702","6703","6724","6752","6758",
    "6762","6770","6841","6857","6861","6902","6952","6954","6971","6976",
    "6981","7003","7004","7011","7012","7013","7182","7201","7202","7203",
    "7205","7211","7261","7267","7269","7270","7272","7731","7733","7735",
    "7741","7751","7752","7762","7832","7911","7912","7951","7974","8001",
    "8002","8003","8015","8031","8035","8053","8058","8113","8174","8253",
    "8267","8303","8304","8306","8308","8309","8316","8331","8354","8355",
    "8377","8381","8385","8411","8591","8601","8604","8630","8697","8725",
    "8750","8766","8795","8801","8802","8803","8830","9001","9005","9007",
    "9008","9009","9020","9021","9022","9062","9064","9101","9104","9107",
    "9202","9301","9432","9433","9434","9501","9502","9503","9531","9532",
    "9602","9613","9706","9735","9766","9983","9984",
]

def japonya_listesi_cek():
    try:
        import FinanceDataReader as fdr
        df = fdr.StockListing("TSE")
        semboller = [str(s).strip() for s in df["Symbol"].dropna().tolist() if str(s).strip()]
        semboller = list(dict.fromkeys(semboller))[:1500]
        if len(semboller) >= 100:
            print(f"Japonya (TSE): {len(semboller)} hisse")
            return semboller
    except Exception as e:
        print(f"TSE hatası: {e}")
    print(f"Japonya sabit liste: {len(JAPONYA_LISTE)} hisse")
    return JAPONYA_LISTE

# ─────────────────────────────────────────────
# HONG KONG LİSTESİ
# ─────────────────────────────────────────────
HONGKONG_LISTE = [
    "0001","0002","0003","0005","0006","0011","0012","0016","0017","0019",
    "0023","0027","0066","0083","0101","0135","0144","0151","0175","0241",
    "0267","0285","0288","0291","0358","0371","0386","0388","0522","0570",
    "0656","0659","0669","0688","0700","0762","0823","0836","0857","0868",
    "0883","0914","0939","0941","0960","0992","1024","1038","1044","1093",
    "1109","1113","1171","1177","1199","1288","1299","1308","1357","1378",
    "1398","1810","1876","1918","1928","1997","2007","2018","2020","2313",
    "2318","2319","2382","2388","2628","2800","3328","3618","3690","3988",
    "6098","6618","6837","6862","9888","9999","0004","0007","0008","0009",
    "0010","0013","0014","0015","0018","0020","0021","0022","0024","0025",
]

def hongkong_listesi_cek():
    print(f"Hong Kong sabit liste: {len(HONGKONG_LISTE)} hisse")
    return HONGKONG_LISTE

# ─────────────────────────────────────────────
# ALMANYA LİSTESİ — GitHub almanya.txt
# ─────────────────────────────────────────────
ALMANYA_YEDEK = [
    "SAP","SIE","ALV","BMW","MBG","BAS","BAYN","DTE","RWE","DBK",
    "ADS","MUV2","IFX","VOW3","FRE","HEN3","MRK","PUM","ZAL","DPW",
    "RHM","AIR","QIA","SHL","VNA","1COV","BNR","CON","P911","DHER",
]

def almanya_listesi_cek():
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/almanya.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            semboller = [
                line.strip().upper()
                for line in r.text.splitlines()
                if line.strip() and not line.startswith("#")
            ]
            semboller = list(dict.fromkeys(semboller))
            if len(semboller) >= 20:
                print(f"Almanya: {len(semboller)} hisse")
                return semboller
    except Exception as e:
        print(f"almanya.txt hatası: {e}")
    return ALMANYA_YEDEK

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

# ─────────────────────────────────────────────
# TVDATAFEEd VERİ ÇEK
# ─────────────────────────────────────────────
def tv_veri_cek(sembol, borsa, deneme=0):
    try:
        df = tv.get_hist(
            symbol=sembol,
            exchange=borsa,
            interval=Interval.in_4_hour,
            n_bars=N_BARS,
        )
        if df is None or len(df) < 50:
            return None

        df = df.rename(columns={
            "open": "Open", "high": "High",
            "low": "Low", "close": "Close", "volume": "Volume"
        })
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

        if len(df) < 50:
            return None
        return df

    except Exception as e:
        if deneme < 2:
            time.sleep(2)
            return tv_veri_cek(sembol, borsa, deneme + 1)
        return None

# ─────────────────────────────────────────────
# HACİM FİLTRESİ
# ─────────────────────────────────────────────
def hacim_gecti(df, tip):
    try:
        ort = df.tail(18)["Volume"].mean()
        if tip == "japonya":   return ort >= JAPONYA_HACIM
        if tip == "hongkong":  return ort >= HONGKONG_HACIM
        if tip == "almanya":   return ort >= ALMANYA_HACIM
        return True
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
def hisse_tara(sembol, borsa, tip):
    try:
        df = tv_veri_cek(sembol, borsa)
        if df is None:
            return False
        if not hacim_gecti(df, tip):
            return False

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return False
        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                return False

        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False
        for i in range(alma_bars - 1, -1, -1):
            if alma4[-1 - i] < alma9[-1 - i]:
                return False

        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None or rsi_vals[-1] > RSI_MAX:
            return False
        for i in range(rsi_bars - 1, -1, -1):
            if rsi_vals[-1 - i] < rsi_sma[-1 - i]:
                return False

        mid, lower, upper = nw_envelope(close, h=8.0, mult=3.0)
        zone = lower + (mid - lower) * NW_ZONE
        if close[-1] > zone or close[-1] < lower:
            return False

        return True

    except Exception as e:
        print(f"{sembol} hata: {e}")
        return False

# ─────────────────────────────────────────────
# ANA TARAMA
# ─────────────────────────────────────────────
def tara(jp_listesi, hk_listesi, de_listesi):
    toplam = len(jp_listesi) + len(hk_listesi) + len(de_listesi)
    print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Tarama başladı — {toplam} sembol")
    bulunanlar_jp = []
    bulunanlar_hk = []
    bulunanlar_de = []

    for i, sembol in enumerate(jp_listesi):
        print(f"  [JP {i+1}/{len(jp_listesi)}] {sembol}", end=" ", flush=True)
        if hisse_tara(sembol, "TSE", "japonya"):
            print("✓ SİNYAL")
            bulunanlar_jp.append(sembol)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    for i, sembol in enumerate(hk_listesi):
        print(f"  [HK {i+1}/{len(hk_listesi)}] {sembol}", end=" ", flush=True)
        if hisse_tara(sembol, "HKEX", "hongkong"):
            print("✓ SİNYAL")
            bulunanlar_hk.append(sembol)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    for i, sembol in enumerate(de_listesi):
        print(f"  [DE {i+1}/{len(de_listesi)}] {sembol}", end=" ", flush=True)
        if hisse_tara(sembol, "XETR", "almanya"):
            print("✓ SİNYAL")
            bulunanlar_de.append(sembol)
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

    telegram_gonder(
        f"🤖 <b>Bot 3 — Asya/Avrupa Başlatıldı!</b>\n\n"
        f"🇯🇵 Japonya: {len(jp_listesi)} hisse\n"
        f"🇭🇰 Hong Kong: {len(hk_listesi)} hisse\n"
        f"🇩🇪 Almanya: {len(de_listesi)} hisse\n"
        f"📡 Veri: TradingView (tvDatafeed)\n\n"
        f"<b>Filtreler:</b>\n"
        f"• Japonya Hacim ≥ 750M JPY\n"
        f"• Hong Kong Hacim ≥ 5M USD\n"
        f"• Almanya Hacim ≥ 5M EUR\n"
        f"• Fisher crossover (2 mum, 0 altı)\n"
        f"• ALMA 4/9 crossover (2 mum)\n"
        f"• RSI ≤ 40\n"
        f"• NW Envelope alt %10"
    )

    while True:
        jp_listesi = japonya_listesi_cek()
        hk_listesi = hongkong_listesi_cek()
        de_listesi = almanya_listesi_cek()
        tara(jp_listesi, hk_listesi, de_listesi)
        print("\nYeni tur başlıyor...\n")
        time.sleep(60)
