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
N_BARS         = 500

# tvDatafeed bağlantısı
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
            json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram hatası: {e}")

# ─────────────────────────────────────────────
# TVDATAFEED VERİ ÇEK
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
                "open": "Open", "high": "High",
                "low": "Low", "close": "Close", "volume": "Volume"
            })
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            if len(df) >= 50:
                return df
    except Exception:
        if deneme < 1:
            time.sleep(2)
            return tv_veri_cek(sembol, borsa, deneme + 1)
    return None

# ─────────────────────────────────────────────
# HACİM FİLTRESİ
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
            0.66 * ((hl2[i] - low_[i]) / denom - 0.5) + 0.67 * val[i - 1]
            if denom != 0 and not np.isnan(denom) else 0.67 * val[i - 1]
        )
        val[i]   = max(min(raw, 0.999), -0.999)
        fish1[i] = 0.5 * np.log((1 + val[i]) / (1 - val[i])) + 0.5 * fish1[i - 1]

    fish2    = np.roll(fish1, 1)
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

    weights = np.array([np.exp(-(i ** 2) / (h * h * 2)) for i in range(max_lookback)], dtype=float)
    weights = weights / weights.sum()

    for idx in range(n):
        usable = min(idx + 1, max_lookback)
        w = weights[:usable]
        w = w / w.sum()

        window = close[idx - usable + 1: idx + 1]
        out = np.dot(window[::-1], w)
        nw_out[idx] = out

    abs_diff = np.abs(close - nw_out)
    mae = pd.Series(abs_diff).rolling(499, min_periods=499).mean().values * mult

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
        return False

    if nw_bar > 0:
        for j in range(nw_bar - 1, -1, -1):
            idx = n - 1 - j
            if idx < 0:
                continue
            if np.isnan(zone[idx]) or np.isnan(lower[idx]):
                continue

            if close[idx] > zone[idx] or close[idx] < lower[idx]:
                return False

    return True

# ─────────────────────────────────────────────
# SİNYAL DETAYI HESAPLA
# ─────────────────────────────────────────────
def sinyal_detayi_uret(df):
    close = float(df["Close"].iloc[-1])
    sinyal_zamani = pd.Timestamp(df.index[-1])

    stop_fiyat = close * (1 - STOP_PCT / 100.0)
    take_fiyat = close * (1 + TAKE_PCT / 100.0)

    # Hisse piyasasında tam kesin tarih değil; yaklaşık takvim hesabı
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
            return None

        if not hacim_gecti(df):
            return None

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        # 1) FISHER
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2, MAX_BARS)
        if fisher_bars is None:
            return None

        if fish1[-1 - fisher_bars] >= 0:
            return None

        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                return None

        # 2) ALMA
        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9, MAX_BARS)
        if alma_bars is None:
            return None

        for i in range(alma_bars - 1, -1, -1):
            if alma4[-1 - i] < alma9[-1 - i]:
                return None

        # 3) RSI
        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma, MAX_BARS)
        if rsi_bars is None:
            return None

        if rsi_vals[-1 - rsi_bars] > RSI_MAX:
            return None

        for i in range(rsi_bars - 1, -1, -1):
            if rsi_vals[-1 - i] < rsi_sma[-1 - i]:
                return None

        # 4) NW ENVELOPE
        _, lower, _, zone = nw_serileri(close, h=8.0, mult=3.0)
        if not nw_touch_and_reverse(close, zone, lower, MAX_BARS):
            return None

        detay = sinyal_detayi_uret(df)
        detay["ticker"] = ticker
        detay["borsa"] = borsa
        return detay

    except Exception as e:
        print(f"{ticker} hata: {e}")
        return None

# ─────────────────────────────────────────────
# ANA TARAMA
# ─────────────────────────────────────────────
def tara(hisse_listesi):
    print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Tarama başladı — {len(hisse_listesi)} hisse")
    bulunanlar = []

    for i, (ticker, borsa) in enumerate(hisse_listesi):
        print(f"  [{i+1}/{len(hisse_listesi)}] {ticker}({borsa})", end=" ", flush=True)
        sonuc = hisse_tara(ticker, borsa)
        if sonuc:
            print("✓ SİNYAL")
            bulunanlar.append(sonuc)
        else:
            print("✗")
        time.sleep(random.uniform(BEKLEME_MIN, BEKLEME_MAX))

    if bulunanlar:
        mesaj = "🇺🇸 <b>ABD AL Sinyali!</b>\n\n"
        mesaj += f"⏰ Tarama: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        mesaj += f"📡 Veri: TradingView\n"
        mesaj += f"⚙️ Set: 2 / 70 / 1.0 / 200 / 15 / 30\n\n"

        for s in bulunanlar:
            mesaj += (
                f"<b>{s['ticker']}</b> ({s['borsa']})\n"
                f"• Alış: <b>{s['alis']:.2f}</b>\n"
                f"• Take-Profit (%30): <b>{s['take']:.2f}</b>\n"
                f"• Stop-Loss (%15): <b>{s['stop']:.2f}</b>\n"
                f"• Sinyal zamanı: <b>{s['sinyal_zamani'].strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"• En geç çıkış: <b>{EXIT_BARS} adet 4 saatlik mum sonra</b>\n"
                f"• Tahmini son tarih: <b>{s['tahmini_son_cikis'].strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            )

        mesaj += "ℹ️ Not: 'Tahmini son tarih' 4 saat × 200 üzerinden yaklaşık hesaplanır."
        telegram_gonder(mesaj)
    else:
        print("\nSinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    abd_listesi = abd_listesi_cek()

    telegram_gonder(
        f"🤖 <b>Bot 2 — ABD Borsası Başlatıldı!</b>\n\n"
        f"🔢 Toplam hisse: {len(abd_listesi)}\n"
        f"📡 Veri: TradingView (tvDatafeed)\n\n"
        f"<b>Filtreler:</b>\n"
        f"• Hacim ≥ 10M USD\n"
        f"• Fisher crossover (2 mum, 0 altı)\n"
        f"• ALMA 4/9 crossover (2 mum)\n"
        f"• RSI crossover + RSI ≤ 70\n"
        f"• NW Envelope bölge ≤ 1.0\n"
        f"• NW bozulursa sinyal iptal\n\n"
        f"<b>Notlar:</b>\n"
        f"• Stop-Loss: %15\n"
        f"• Take-Profit: %30\n"
        f"• En geç çıkış: 200 adet 4 saatlik mum"
    )

    while True:
        abd_listesi = abd_listesi_cek()
        tara(abd_listesi)
        print("\nYeni tur başlıyor...\n")
        time.sleep(60)
