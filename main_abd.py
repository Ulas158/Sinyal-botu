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

# STRATEJİ SETİ
MAX_BARS       = 2
RSI_MAX        = 70.0
NW_ZONE        = 1.0
EXIT_BARS      = 200
STOP_PCT       = 15.0
TAKE_PCT       = 30.0

BEKLEME_MIN    = 1.5
BEKLEME_MAX    = 3.0
ABD_HACIM_MIN  = 10_000_000
N_BARS         = 700

# DEBUG / TEST
TEST_MODE         = True
DEBUG_TICKER      = "AAPL"
DEBUG_SKIP_VOLUME = True

# Geçmiş bar testi
# TradingView'deki entry zamanını buraya yaz
# Örnek: "2026-02-17 20:00:00"
TEST_TARGET_TIME  = "2026-02-17 20:00:00"

# ─────────────────────────────────────────────
# TVDATAFEED BAĞLANTI
# ─────────────────────────────────────────────
try:
    if TV_USERNAME and TV_PASSWORD:
        tv = TvDatafeed(TV_USERNAME, TV_PASSWORD)
        print("TradingView hesabıyla bağlandı ✓")
    else:
        tv = TvDatafeed()
        print("TradingView anonim bağlandı ✓")
except Exception:
    tv = TvDatafeed()

# ─────────────────────────────────────────────
# ABD LİSTESİ — GitHub abd.txt
# ─────────────────────────────────────────────
ABD_YEDEK = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","MA",
    "JNJ","XOM","WMT","PG","HD","BAC","ABBV","MRK","CVX","PFE",
    "NFLX","ADBE","CRM","AMD","INTC","QCOM","TXN","AVGO","ORCL","GE",
    "CAT","BA","GS","MS","C","WFC","AXP","BLK","UNH","LLY",
]

def abd_listesi_cek():
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_USER}/Sinyal-botu/main/abd.txt"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            sonuc = []

            for line in r.text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if ":" in line:
                    parca = line.split(":")
                    sembol = parca[0].strip().upper()
                    borsa  = parca[1].strip().upper()
                else:
                    sembol = line.upper()
                    borsa  = "NASDAQ"

                sonuc.append((sembol, borsa))

            gorulen = set()
            temiz = []

            for s, b in sonuc:
                if s not in gorulen:
                    gorulen.add(s)
                    temiz.append((s, b))

            if len(temiz) >= 20:
                print(f"ABD: {len(temiz)} hisse")
                return temiz

        raise Exception(f"HTTP {r.status_code}")

    except Exception as e:
        print(f"abd.txt hatası: {e} — yedek liste")
        return [(s, "NASDAQ") for s in ABD_YEDEK]

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def telegram_gonder(mesaj):
    if not TELEGRAM_TOKEN:
        print("Telegram token yok, mesaj gönderilmedi.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": mesaj,
                "parse_mode": "HTML"
            },
            timeout=10
        )
    except Exception as e:
        print(f"Telegram hatası: {e}")

# ─────────────────────────────────────────────
# DEBUG
# ─────────────────────────────────────────────
def dprint(ticker, msg):
    if TEST_MODE and ticker == DEBUG_TICKER:
        print(msg)

# ─────────────────────────────────────────────
# VERİ
# ─────────────────────────────────────────────
def tv_veri_cek(sembol, borsa="NASDAQ", deneme=0):
    try:
        df = tv.get_hist(
            symbol=sembol,
            exchange=borsa,
            interval=Interval.in_4_hour,
            n_bars=N_BARS,
        )

        if df is not None and len(df) >= 50:
            df = df.rename(columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            })
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

            if len(df) >= 50:
                return df

    except Exception:
        if deneme < 1:
            time.sleep(2)
            return tv_veri_cek(sembol, borsa, deneme + 1)

    return None

def test_barina_kes(df, target_time_str):
    """
    Geçmişteki belirli bir barı son bar kabul etmek için df'yi o bar dahil olacak şekilde keser.
    """
    ts = pd.Timestamp(target_time_str)
    df2 = df[df.index <= ts].copy()

    if len(df2) == 0:
        return None

    if df2.index[-1] != ts:
        # Tam eşleşme yoksa en yakın önceki barı kullan
        print(f"UYARI: tam bar bulunamadı, kullanılan son bar: {df2.index[-1]}")
    else:
        print(f"TEST BAR BULUNDU: {df2.index[-1]}")

    return df2

# ─────────────────────────────────────────────
# HACİM
# ─────────────────────────────────────────────
def hacim_gecti(df):
    try:
        return df.tail(18)["Volume"].mean() >= ABD_HACIM_MIN
    except Exception:
        return False

# ─────────────────────────────────────────────
# İNDİKATÖRLER
# ─────────────────────────────────────────────
def alma(src, length, offset=0.85, sigma=6.0):
    m = offset * (length - 1)
    s = length / sigma

    weights = np.array(
        [np.exp(-((i - m) ** 2) / (2 * s * s)) for i in range(length)],
        dtype=float
    )
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

        if denom != 0 and not np.isnan(denom):
            raw = 0.66 * ((hl2[i] - low_[i]) / denom - 0.5) + 0.67 * val[i - 1]
        else:
            raw = 0.67 * val[i - 1]

        val[i] = max(min(raw, 0.999), -0.999)
        fish1[i] = 0.5 * np.log((1 + val[i]) / (1 - val[i])) + 0.5 * fish1[i - 1]

    fish2 = np.roll(fish1, 1)
    fish2[0] = np.nan

    return fish1, fish2

def rsi_hesapla(close, length=14):
    delta = pd.Series(close).diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_g = gain.ewm(alpha=1 / length, min_periods=length).mean()
    avg_l = loss.ewm(alpha=1 / length, min_periods=length).mean()
    rs    = avg_g / avg_l
    return (100 - 100 / (1 + rs)).values

def nw_serileri(close, h=8.0, mult=3.0):
    close = np.asarray(close, dtype=float)
    n = len(close)

    nw_out   = np.full(n, np.nan)
    nw_lower = np.full(n, np.nan)
    nw_upper = np.full(n, np.nan)
    nw_zone  = np.full(n, np.nan)

    max_lookback = min(500, n)

    weights = np.array(
        [np.exp(-(i ** 2) / (h * h * 2)) for i in range(max_lookback)],
        dtype=float
    )
    weights /= weights.sum()

    for idx in range(n):
        usable = min(idx + 1, max_lookback)
        w = weights[:usable]
        w = w / w.sum()

        window = close[idx - usable + 1: idx + 1]
        out = np.dot(window[::-1], w)
        nw_out[idx] = out

    mae = pd.Series(np.abs(close - nw_out)).rolling(499, min_periods=499).mean().values * mult

    nw_lower = nw_out - mae
    nw_upper = nw_out + mae
    nw_zone  = nw_lower + (nw_out - nw_lower) * NW_ZONE

    return nw_out, nw_lower, nw_upper, nw_zone

def crossover_bars_ago(a, b, max_bars=MAX_BARS):
    for i in range(max_bars + 1):
        idx = -1 - i

        if len(a) < abs(idx) + 1:
            return None

        try:
            if np.isnan(a[idx]) or np.isnan(b[idx]) or np.isnan(a[idx - 1]) or np.isnan(b[idx - 1]):
                continue

            if a[idx] > b[idx] and a[idx - 1] <= b[idx - 1]:
                return i

        except Exception:
            return None

    return None

def nw_touch_and_reverse(close, zone, lower, max_bars=MAX_BARS):
    n = len(close)
    nw_bar = None

    for i in range(max_bars + 1):
        idx = n - 1 - i
        if idx < 0:
            break

        if np.isnan(zone[idx]) or np.isnan(lower[idx]):
            continue

        if lower[idx] <= close[idx] <= zone[idx]:
            nw_bar = i
            break

    if nw_bar is None:
        return False, None

    if nw_bar > 0:
        for j in range(nw_bar - 1, -1, -1):
            idx = n - 1 - j
            if idx < 0:
                continue

            if np.isnan(zone[idx]) or np.isnan(lower[idx]):
                continue

            if close[idx] > zone[idx] or close[idx] < lower[idx]:
                return False, nw_bar

    return True, nw_bar

# ─────────────────────────────────────────────
# SİNYAL DETAYI
# ─────────────────────────────────────────────
def sinyal_detayi_uret(df):
    close = float(df["Close"].iloc[-1])
    sinyal_zamani = pd.Timestamp(df.index[-1])

    stop_fiyat = close * (1 - STOP_PCT / 100.0)
    take_fiyat = close * (1 + TAKE_PCT / 100.0)
    tahmini_son_cikis = sinyal_zamani + pd.Timedelta(hours=4 * EXIT_BARS)

    return {
        "alis": close,
        "stop": stop_fiyat,
        "take": take_fiyat,
        "sinyal_zamani": sinyal_zamani,
        "tahmini_son_cikis": tahmini_son_cikis,
    }

# ─────────────────────────────────────────────
# HİSSE TARA
# ─────────────────────────────────────────────
def hisse_tara(ticker, borsa="NASDAQ"):
    try:
        df = tv_veri_cek(ticker, borsa)
        if df is None:
            dprint(ticker, "VERI YOK")
            return None

        if TEST_MODE:
            df = test_barina_kes(df, TEST_TARGET_TIME)
            if df is None or len(df) < 50:
                dprint(ticker, "TEST BARINA KESILINCE VERI YETERSIZ")
                return None

        if not hacim_gecti(df):
            dprint(ticker, "HACIM GECMEDI")
            if not DEBUG_SKIP_VOLUME:
                return None
            dprint(ticker, "DEBUG_SKIP_VOLUME aktif, devam ediyorum")

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        dprint(ticker, f"Son bar zamanı: {df.index[-1]}")
        dprint(ticker, f"Son close: {close[-1]:.4f}")

        # 1) FISHER
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars = crossover_bars_ago(fish1, fish2, MAX_BARS)
        dprint(ticker, f"Fisher bars: {fisher_bars}")

        if fisher_bars is None:
            dprint(ticker, "FISHER: crossover yok")
            return None

        dprint(ticker, f"Fisher signal bar fish1: {fish1[-1 - fisher_bars]:.4f}")
        dprint(ticker, f"Fisher signal bar fish2: {fish2[-1 - fisher_bars]:.4f}")

        if fish1[-1 - fisher_bars] >= 0:
            dprint(ticker, "FISHER: 0 alti sarti gecmedi")
            return None

        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                dprint(ticker, f"FISHER: reverse iptal, i={i}")
                return None

        dprint(ticker, "FISHER: GECTI")

        # 2) ALMA
        alma4 = alma(close, 4)
        alma9 = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9, MAX_BARS)
        dprint(ticker, f"ALMA bars: {alma_bars}")

        if alma_bars is None:
            dprint(ticker, "ALMA: crossover yok")
            return None

        dprint(ticker, f"ALMA signal bar alma4: {alma4[-1 - alma_bars]:.4f}")
        dprint(ticker, f"ALMA signal bar alma9: {alma9[-1 - alma
