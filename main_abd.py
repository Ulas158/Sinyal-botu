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

MAX_BARS      = 2
RSI_MAX       = 70.0
NW_ZONE       = 1.0
EXIT_BARS     = 200
STOP_PCT      = 15.0
TAKE_PCT      = 30.0

BEKLEME_MIN   = 1.5
BEKLEME_MAX   = 3.0
ABD_HACIM_MIN = 10_000_000
N_BARS        = 500

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
                    parca  = line.split(":")
                    sembol = parca[0].strip().upper()
                    borsa  = parca[1].strip().upper()
                else:
                    sembol = line.upper()
                    borsa  = "NASDAQ"
                sonuc.append((sembol, borsa))
            gorulen = set()
            temiz   = []
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
        print("Telegram token yok.")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
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
    # TradingView ta.alma() ile birebir aynı formül
    m = offset * (length - 1)
    s = length / sigma
    result = np.full(len(src), np.nan)
    for idx in range(length - 1, len(src)):
        norm = 0.0
        total = 0.0
        for i in range(length):
            w = np.exp(-1 * ((i - m) ** 2) / (2 * s * s))
            norm += w
            total += src[idx - length + 1 + i] * w
        result[idx] = total / norm
    return result

def fisher_transform(high, low, length=9):
    hl2   = (high + low) / 2
    high_ = pd.Series(hl2).rolling(length).max().values
    low_  = pd.Series(hl2).rolling(length).min().values
    val   = np.zeros(len(hl2))
    fish1 = np.zeros(len(hl2))
    for i in range(1, len(hl2)):
        denom = high_[i] - low_[i]
        raw   = (0.66 * ((hl2[i] - low_[i]) / denom - 0.5) + 0.67 * val[i-1]
                 if denom != 0 else 0.67 * val[i-1])
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

def nw_envelope(close, h=8.0, mult=3.0):
    # TradingView ile aynı: 500 bar, ağırlıklı ortalama, SMA-MAE
    n = min(500, len(close))
    weights = np.array([np.exp(-(i**2) / (h * h * 2)) for i in range(n)], dtype=float)
    weights /= weights.sum()
    # Her bar için NW değeri hesapla (MAE için gerekli)
    nw_out = np.full(len(close), np.nan)
    for idx in range(len(close)):
        usable = min(idx + 1, n)
        w = weights[:usable] / weights[:usable].sum()
        window = close[idx - usable + 1: idx + 1]
        nw_out[idx] = np.dot(window[::-1], w)
    # MAE: son 499 barın abs farkının ortalaması (TV: ta.sma(abs, 499))
    abs_diff = np.abs(close - nw_out)
    mae_series = pd.Series(abs_diff).rolling(499, min_periods=1).mean().values
    mae = mae_series[-1] * mult
    mid   = nw_out[-1]
    lower = mid - mae
    upper = mid + mae
    return mid, lower, upper, mae

def crossover_bars_ago(a, b):
    for i in range(MAX_BARS + 1):
        idx = -1 - i
        if len(a) < abs(idx) + 1:
            return None
        if (not np.isnan(a[idx]) and not np.isnan(b[idx]) and
            not np.isnan(a[idx-1]) and not np.isnan(b[idx-1])):
            if a[idx] > b[idx] and a[idx-1] <= b[idx-1]:
                return i
    return None

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
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return None
        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                return None

        # 2) ALMA
        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return None
        for i in range(alma_bars - 1, -1, -1):
            if alma4[-1 - i] < alma9[-1 - i]:
                return None

        # 3) RSI
        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None or rsi_vals[-1 - rsi_bars] > RSI_MAX:
            return None
        for i in range(rsi_bars - 1, -1, -1):
            if rsi_vals[-1 - i] < rsi_sma[-1 - i]:
                return None

        # 4) NW ENVELOPE
        mid, lower, upper, mae = nw_envelope(close, h=8.0, mult=3.0)
        zone = lower + mae * NW_ZONE
        if close[-1] > zone or close[-1] < lower:
            return None

        # Sinyal detayı
        alis_fiyat = float(df["Close"].iloc[-1])
        sinyal_zamani = pd.Timestamp(df.index[-1])
        return {
            "ticker":            ticker,
            "borsa":             borsa,
            "alis":              alis_fiyat,
            "stop":              alis_fiyat * (1 - STOP_PCT / 100),
            "take":              alis_fiyat * (1 + TAKE_PCT / 100),
            "sinyal_zamani":     sinyal_zamani,
            "tahmini_son_cikis": sinyal_zamani + pd.Timedelta(hours=4 * EXIT_BARS),
        }

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
        mesaj  = "🇺🇸 <b>ABD AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        mesaj += f"📡 Veri: TradingView\n"
        mesaj += f"⚙️ Set: {MAX_BARS} mum / RSI≤{RSI_MAX} / NW%{int(NW_ZONE*100)} / SL%{STOP_PCT} / TP%{TAKE_PCT}\n\n"
        for s in bulunanlar:
            mesaj += (
                f"<b>{s['ticker']}</b> ({s['borsa']})\n"
                f"• Alış: <b>{s['alis']:.2f}</b>\n"
                f"• Take-Profit (%{int(TAKE_PCT)}): <b>{s['take']:.2f}</b>\n"
                f"• Stop-Loss (%{int(STOP_PCT)}): <b>{s['stop']:.2f}</b>\n"
                f"• Sinyal: <b>{s['sinyal_zamani'].strftime('%d.%m.%Y %H:%M')}</b>\n"
                f"• Son çıkış: <b>{s['tahmini_son_cikis'].strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            )
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
        f"• Fisher crossover ({MAX_BARS} mum, 0 altı)\n"
        f"• ALMA 4/9 crossover ({MAX_BARS} mum)\n"
        f"• RSI crossover + RSI ≤ {RSI_MAX}\n"
        f"• NW Envelope bölge ≤ {NW_ZONE}\n\n"
        f"<b>Risk:</b>\n"
        f"• Stop-Loss: %{STOP_PCT}\n"
        f"• Take-Profit: %{TAKE_PCT}\n"
        f"• Max çıkış: {EXIT_BARS} × 4H mum"
    )

    while True:
        abd_listesi = abd_listesi_cek()
        tara(abd_listesi)
        print("\nYeni tur başlıyor...\n")
        time.sleep(60)
