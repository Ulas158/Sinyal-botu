import os
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

# ─────────────────────────────────────────────
# AYARLAR — .env dosyasından okunur
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID", "7116490869")
INTERVAL       = "4h"
MAX_BARS       = 3  # Sinyalin geçerli sayılacağı maksimum mum sayısı

# ─────────────────────────────────────────────
# HİSSE LİSTESİ
# ─────────────────────────────────────────────
BIST_HISSELER = [
    "THYAO.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS", "YKBNK.IS",
    "SISE.IS",  "KCHOL.IS", "BIMAS.IS", "EREGL.IS", "TOASO.IS",
    "FROTO.IS", "TTKOM.IS", "SAHOL.IS", "PETKM.IS", "TUPRS.IS",
    "ARCLK.IS", "DOHOL.IS", "EKGYO.IS", "HALKB.IS", "ISCTR.IS",
    "KORDS.IS", "LOGO.IS",  "MGROS.IS", "OTKAR.IS", "PGSUS.IS",
    "SASA.IS",  "SOKM.IS",  "TAVHL.IS", "TCELL.IS", "VAKBN.IS",
    "VESTL.IS", "KOZAL.IS", "ALARK.IS", "CIMSA.IS", "GUBRF.IS",
    "IPEKE.IS", "KARSN.IS", "KONTR.IS", "MAVI.IS",  "NETAS.IS",
    "ODAS.IS",  "OYAKC.IS", "QUAGR.IS", "RAYSG.IS", "SKBNK.IS",
    "TKFEN.IS", "TSKB.IS",  "ULKER.IS", "ZOREN.IS", "AEFES.IS",
]

ABD_HISSELER = [
    "AAPL",  "MSFT",  "NVDA",  "GOOGL", "AMZN",
    "META",  "TSLA",  "BRK-B", "JPM",   "V",
    "UNH",   "XOM",   "LLY",   "JNJ",   "MA",
    "AVGO",  "PG",    "HD",    "MRK",   "COST",
    "ABBV",  "CVX",   "PEP",   "KO",    "ADBE",
    "WMT",   "BAC",   "CRM",   "MCD",   "TMO",
    "CSCO",  "ACN",   "ABT",   "LIN",   "DHR",
    "TXN",   "NEE",   "PM",    "ORCL",  "RTX",
    "QCOM",  "HON",   "UPS",   "AMGN",  "IBM",
    "GS",    "CAT",   "INTU",  "SPGI",  "BLK",
]

TUM_HISSELER = BIST_HISSELER + ABD_HISSELER

# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────
def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"})
    except Exception as e:
        print(f"Telegram hatası: {e}")

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
        raw = 0.66 * ((hl2[i] - low_[i]) / (high_[i] - low_[i] + 1e-10) - 0.5) + 0.67 * val[i-1]
        val[i] = max(min(raw, 0.999), -0.999)
        fish1[i] = 0.5 * np.log((1 + val[i]) / (1 - val[i])) + 0.5 * fish1[i-1]
    fish2 = np.roll(fish1, 1)
    fish2[0] = np.nan
    return fish1, fish2

def rsi(close, length=14):
    delta  = pd.Series(close).diff()
    gain   = delta.clip(lower=0)
    loss   = -delta.clip(upper=0)
    avg_g  = gain.ewm(alpha=1/length, min_periods=length).mean()
    avg_l  = loss.ewm(alpha=1/length, min_periods=length).mean()
    rs     = avg_g / avg_l
    return (100 - 100 / (1 + rs)).values

def nw_envelope(close, h=8.0, mult=3.0, n=200):
    src = close[-n:]
    def gauss(x): return np.exp(-(x**2) / (h * h * 2))
    weights = np.array([gauss(i) for i in range(n)])
    weights /= weights.sum()
    out = np.dot(src[::-1], weights)
    mae = np.mean(np.abs(src - out)) * mult
    return out, out - mae, out + mae  # mid, lower, upper

# ─────────────────────────────────────────────
# CROSSOVER YARDIMCI
# ─────────────────────────────────────────────
def crossover_bars_ago(a, b, max_bars=MAX_BARS):
    """a dizisi b dizisini yukarı kestiyse, kaç bar önce? max_bars'tan büyükse None."""
    for i in range(max_bars + 1):
        idx = -1 - i
        if len(a) < abs(idx) + 1:
            return None
        if a[idx] > b[idx] and a[idx-1] <= b[idx-1]:
            return i
    return None

# ─────────────────────────────────────────────
# TEK HİSSE TARAMA
# ─────────────────────────────────────────────
def hisse_tara(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=True)
        if df is None or len(df) < 50:
            return False

        # Çoklu seviye sütunları düzelt
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [c.capitalize() for c in df.columns]

        # 4 saatlik mum oluştur
        df = df.resample("4h").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        if len(df) < 50:
            return False

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        # 1) FISHER
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None:
            return False
        # Kesişim anında fish1 < 0 olmalı
        idx = -1 - fisher_bars
        if fish1[idx] >= 0:
            return False

        # 2) ALMA 4/9
        alma4 = alma(close, 4)
        alma9 = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False

        # 3) RSI — RSI SMA'yı yukarı kessin ve RSI <= 50
        rsi_vals = rsi(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None:
            return False
        if rsi_vals[-1] > 50:
            return False

        # 4) NW ENVELOPE — fiyat alt bandın alt %30'unda
        mid, lower, upper = nw_envelope(close, h=8.0, mult=3.0)
        zone30 = lower + (mid - lower) * 0.30
        if close[-1] > zone30 or close[-1] < lower:
            return False

        return True

    except Exception as e:
        print(f"{ticker} hata: {e}")
        return False

# ─────────────────────────────────────────────
# ANA TARAMA DÖNGÜSÜ
# ─────────────────────────────────────────────
def tara():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama başladı — {len(TUM_HISSELER)} hisse")
    bulunanlar = []

    for ticker in TUM_HISSELER:
        print(f"  → {ticker}", end=" ")
        if hisse_tara(ticker):
            print("✓ SİNYAL")
            bulunanlar.append(ticker)
        else:
            print("✗")
        time.sleep(0.5)  # rate limit için bekle

    if bulunanlar:
        mesaj = "🟢 <b>AL Sinyali Tespit Edildi!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        mesaj += f"📊 Zaman Dilimi: 4 Saatlik\n\n"
        mesaj += "<b>Hisseler:</b>\n"
        for h in bulunanlar:
            mesaj += f"  • {h.replace('.IS', '')} \n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI + NW Envelope"
        telegram_gonder(mesaj)
        print(f"Telegram gönderildi: {bulunanlar}")
    else:
        print("Sinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    telegram_gonder("🤖 Sinyal botu başlatıldı!\n4 saatlik tarama aktif.")
    while True:
        tara()
        print("4 saat bekleniyor...\n")
        time.sleep(4 * 60 * 60)  # 4 saat
