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
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID          = os.environ.get("CHAT_ID", "7116490869")
GITHUB_USER      = os.environ.get("GITHUB_USER", "Ulas158")
TV_USERNAME      = os.environ.get("TV_USERNAME", "")   # TradingView kullanıcı adı (opsiyonel)
TV_PASSWORD      = os.environ.get("TV_PASSWORD", "")   # TradingView şifre (opsiyonel)
MAX_BARS         = 2
RSI_MAX          = 40.0
NW_ZONE          = 0.10
BEKLEME_MIN      = 1.5
BEKLEME_MAX      = 3.0
BIST_HACIM_MIN   = 20_000_000
KRIPTO_HACIM_MIN = 10_000_000
N_BARS           = 500   # Kaç mum çekilsin

# tvDatafeed bağlantısı
try:
    if TV_USERNAME and TV_PASSWORD:
        tv = TvDatafeed(TV_USERNAME, TV_PASSWORD)
        print("TradingView hesabıyla bağlandı ✓")
    else:
        tv = TvDatafeed()
        print("TradingView anonim bağlandı ✓")
except Exception as e:
    print(f"tvDatafeed bağlantı hatası: {e}")
    tv = TvDatafeed()

# ─────────────────────────────────────────────
# BIST — GitHub bist.txt
# ─────────────────────────────────────────────
BIST_YEDEK = [
    "THYAO","ASELS","EREGL","KCHOL","SASA","TCELL","GARAN","AKBNK","YKBNK",
    "ARCLK","FROTO","TOASO","SAHOL","KOZAL","TUPRS","PETKM","VESTL","ENKAI",
    "EKGYO","ISCTR","HALKB","VAKBN","TKFEN","TSKB","LOGO","MGROS","TTKOM",
    "TAVHL","CCOLA","DOAS","SISE","KCHOL","BIMAS","ULKER","AEFES","AKSA",
]

def bist_listesi_cek():
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/bist.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            semboller = [
                line.strip().upper()
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
        return BIST_YEDEK

# ─────────────────────────────────────────────
# KRİPTO — GitHub kripto.txt
# ─────────────────────────────────────────────
KRIPTO_YEDEK = [
    "BTC","ETH","BNB","XRP","SOL","ADA","DOGE","TRX","TON","LINK",
    "AVAX","DOT","LTC","BCH","NEAR","UNI","APT","ETC","XLM","ATOM",
    "AAVE","OP","ARB","FIL","INJ","SAND","AXS","ALGO","RUNE","DASH",
]

def kripto_listesi_cek():
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/kripto.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            semboller = [
                line.strip().upper()
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

        # Kolon isimlerini düzelt
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
        ort_hacim = df.tail(18)["Volume"].mean()
        if tip == "bist":
            return ort_hacim >= BIST_HACIM_MIN
        elif tip == "kripto":
            return ort_hacim >= KRIPTO_HACIM_MIN
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

        # 1) FISHER
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return False
        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                return False

        # 2) ALMA 4/9
        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False
        for i in range(alma_bars - 1, -1, -1):
            if alma4[-1 - i] < alma9[-1 - i]:
                return False

        # 3) RSI
        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None or rsi_vals[-1] > RSI_MAX:
            return False
        for i in range(rsi_bars - 1, -1, -1):
            if rsi_vals[-1 - i] < rsi_sma[-1 - i]:
                return False

        # 4) NW ENVELOPE
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
def tara(bist_listesi, kripto_listesi):
    toplam = len(bist_listesi) + len(kripto_listesi)
    print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Tarama başladı — {toplam} sembol")
    bulunanlar_bist   = []
    bulunanlar_kripto = []

    # BIST
    for i, sembol in enumerate(bist_listesi):
        print(f"  [BIST {i+1}/{len(bist_listesi)}] {sembol}", end=" ", flush=True)
        if hisse_tara(sembol, "BIST", "bist"):
            print("✓ SİNYAL")
            bulunanlar_bist.append(sembol)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    # KRİPTO (Binance'de USDT parite)
    for i, sembol in enumerate(kripto_listesi):
        binance_sembol = sembol + "USDT"
        print(f"  [KRİPTO {i+1}/{len(kripto_listesi)}] {binance_sembol}", end=" ", flush=True)
        if hisse_tara(binance_sembol, "BINANCE", "kripto"):
            print("✓ SİNYAL")
            bulunanlar_kripto.append(sembol)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    # Telegram
    if bulunanlar_bist:
        mesaj = "🇹🇷 <b>BIST AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        for h in bulunanlar_bist:
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

    if not bulunanlar_bist and not bulunanlar_kripto:
        print("\nSinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bist_listesi   = bist_listesi_cek()
    kripto_listesi = kripto_listesi_cek()

    telegram_gonder(
        f"🤖 <b>Bot 1 — BIST + Kripto Başlatıldı!</b>\n\n"
        f"🇹🇷 BIST: {len(bist_listesi)} hisse\n"
        f"🪙 Kripto: {len(kripto_listesi)} coin\n"
        f"📡 Veri: TradingView (tvDatafeed)\n\n"
        f"<b>Filtreler:</b>\n"
        f"• BIST Hacim ≥ 20M TL\n"
        f"• Kripto Hacim ≥ 10M USD\n"
        f"• Fisher crossover (2 mum, 0 altı)\n"
        f"• ALMA 4/9 crossover (2 mum)\n"
        f"• RSI ≤ 40\n"
        f"• NW Envelope alt %10"
    )

    while True:
        bist_listesi   = bist_listesi_cek()
        kripto_listesi = kripto_listesi_cek()
        tara(bist_listesi, kripto_listesi)
        print("\nYeni tur başlıyor...\n")
        time.sleep(60)
