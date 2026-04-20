import os
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

# ─────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID         = os.environ.get("CHAT_ID", "7116490869")
MAX_BARS        = 2       # Fisher ve ALMA crossover max mum
RSI_MAX         = 40.0    # RSI maksimum
NW_ZONE         = 0.10    # NW Envelope alt %10
BEKLEME         = 2.0     # Saniye
RETRY           = 3
HACIM_GUN       = 3       # Son 3 günün ortalama hacmi

BIST_HACIM_MIN   = 20_000_000   # 20 milyon TL
ABD_HACIM_MIN    = 10_000_000   # 10 milyon dolar
KRIPTO_HACIM_MIN = 10_000_000   # 10 milyon dolar

# ─────────────────────────────────────────────
# BIST
# ─────────────────────────────────────────────
BIST = [
    "AEFES.IS","AGESA.IS","AHGAZ.IS","AKENR.IS","AKBNK.IS","AKFEN.IS","AKGRT.IS",
    "AKSA.IS","AKSEN.IS","ALARK.IS","ALBRK.IS","ALGYO.IS","ALKIM.IS","ANACM.IS",
    "ANELE.IS","ANHYT.IS","ANSGR.IS","ARCLK.IS","ARSAN.IS","ASELS.IS","ASTOR.IS",
    "AYEN.IS","AYGAZ.IS","BAGFS.IS","BERA.IS","BIOEN.IS","BIZIM.IS","BJKAS.IS",
    "BNTAS.IS","BOSSA.IS","BRISA.IS","BRKSN.IS","BSOKE.IS","BTCIM.IS","BUCIM.IS",
    "BURCE.IS","BURVA.IS","CANTE.IS","CCOLA.IS","CELHA.IS","CEMAS.IS","CEMTS.IS",
    "CIMSA.IS","CLEBI.IS","COKAS.IS","CRFSA.IS","CUSAN.IS","DAGI.IS","DARDL.IS",
    "DENGE.IS","DESA.IS","DEVA.IS","DITAS.IS","DMSAS.IS","DOAS.IS","DOBUR.IS",
    "DOGUB.IS","DOKTA.IS","DYOBY.IS","DZGYO.IS","ECILC.IS","ECZYT.IS","EDIP.IS",
    "EGEEN.IS","EGEPO.IS","EGGUB.IS","EGPRO.IS","EKGYO.IS","ENJSA.IS","ENKAI.IS",
    "EPLAS.IS","ERBOS.IS","EREGL.IS","ERSU.IS","ESCAR.IS","ESEN.IS","ETILR.IS",
    "EUHOL.IS","EUPWR.IS","EUYO.IS","FADE.IS","FENER.IS","FONET.IS","FRIGO.IS",
    "FROTO.IS","GARAN.IS","GARFA.IS","GEDZA.IS","GENIL.IS","GEREL.IS","GLYHO.IS",
    "GMTAS.IS","GOODY.IS","GOZDE.IS","GRSEL.IS","GSDHO.IS","GSRAY.IS","GUBRF.IS",
    "GWIND.IS","HATEK.IS","HEDEF.IS","HEKTS.IS","HALKB.IS","HLGYO.IS","HOROZ.IS",
    "HUBVC.IS","HUNER.IS","HURGZ.IS","ICBCT.IS","INDES.IS","INVEO.IS","IPEKE.IS",
    "ISATR.IS","ISBIR.IS","ISFIN.IS","ISGYO.IS","ISKPL.IS","ISCTR.IS","ISYAT.IS",
    "ITTFK.IS","IZFAS.IS","IZMDC.IS","JANTS.IS","KAPLM.IS","KARTN.IS","KARSN.IS",
    "KATMR.IS","KAYSE.IS","KENT.IS","KERVT.IS","KCHOL.IS","KGYO.IS","KLGYO.IS",
    "KLKIM.IS","KMPUR.IS","KOCMT.IS","KONYA.IS","KONTR.IS","KOPOL.IS","KRDMD.IS",
    "KRTEK.IS","KOZAL.IS","KUTPO.IS","LIDER.IS","LOGO.IS","MAALT.IS","MAGEN.IS",
    "MARTI.IS","MAVI.IS","MAZGL.IS","MEDTR.IS","MEGAP.IS","MERCN.IS","MERIT.IS",
    "MERKO.IS","METRO.IS","MGROS.IS","MIPAZ.IS","MNDRS.IS","MOBTL.IS","MOGAN.IS",
    "MSGYO.IS","MTRKS.IS","NATEN.IS","NETAS.IS","NIBAS.IS","NTTUR.IS","NUHCM.IS",
    "OBASE.IS","ODAS.IS","ONCSM.IS","ORCAY.IS","ORGE.IS","OSMEN.IS","OSTIM.IS",
    "OTKAR.IS","OTTO.IS","OYAKC.IS","OYAYO.IS","OYLUM.IS","OZGYO.IS","OZKGY.IS",
    "PAGYO.IS","PAMEL.IS","PAPIL.IS","PARSN.IS","PEGYO.IS","PEKMT.IS","PENGD.IS",
    "PENTA.IS","PETKM.IS","PETUN.IS","PGSUS.IS","PINSU.IS","PKART.IS","PLTUR.IS",
    "POLHO.IS","PRZMA.IS","PTOFS.IS","QUAGR.IS","RAYSG.IS","RNPOL.IS","RODRG.IS",
    "ROYAL.IS","RUBNS.IS","RYGYO.IS","SAFKR.IS","SAHOL.IS","SANEL.IS","SANFM.IS",
    "SANKO.IS","SARKY.IS","SASA.IS","SAYAS.IS","SEGYO.IS","SEKUR.IS","SELEC.IS",
    "SELGD.IS","SELVA.IS","SILVR.IS","SISE.IS","SNGYO.IS","SNPAM.IS","SODSN.IS",
    "SOKM.IS","SSTEK.IS","SUWEN.IS","TATGD.IS","TATEN.IS","TAVHL.IS","TBORG.IS",
    "TCELL.IS","TEKTU.IS","TERA.IS","TGSAS.IS","THYAO.IS","TKFEN.IS","TKNSA.IS",
    "TLMAN.IS","TMPOL.IS","TOASO.IS","TRCAS.IS","TRILC.IS","TSGYO.IS","TSKB.IS",
    "TTKOM.IS","TTRAK.IS","TUCLK.IS","TUKAS.IS","TUPRS.IS","TURSG.IS","UFUK.IS",
    "ULUUN.IS","UMPAS.IS","ULKER.IS","UNLU.IS","USAK.IS","VAKBN.IS","VANGD.IS",
    "VBTYZ.IS","VERUS.IS","VESTL.IS","VKFYO.IS","VKGYO.IS","YAPRK.IS","YATAS.IS",
    "YEOTK.IS","YESIL.IS","YGYO.IS","YKBNK.IS","YUNSA.IS","YYAPI.IS","ZEDUR.IS",
    "ZOREN.IS",
]

# ─────────────────────────────────────────────
# NYSE + NASDAQ + DOW + S&P500
# ─────────────────────────────────────────────
ABD = [
    # Mega cap / S&P500 core
    "AAPL","MSFT","NVDA","GOOGL","GOOG","AMZN","META","TSLA","BRK-B","JPM",
    "V","UNH","XOM","LLY","JNJ","MA","AVGO","PG","HD","MRK",
    "COST","ABBV","CVX","PEP","KO","ADBE","WMT","BAC","CRM","MCD",
    "TMO","CSCO","ACN","ABT","LIN","DHR","TXN","NEE","PM","ORCL",
    "RTX","QCOM","HON","UPS","AMGN","IBM","GS","CAT","INTU","SPGI",
    "BLK","ISRG","VRTX","GILD","SYK","REGN","PLD","AMT","CI","LRCX",
    "ADI","MDLZ","MMC","ZTS","MO","DUK","SO","ITW","AON","GE",
    "EQIX","TJX","BSX","CME","NOC","ETN","CL","SHW","MCO","PGR",
    "APD","EMR","WM","FCX","HCA","NSC","ADP","ECL","F","GM",
    "ELV","HUM","FTNT","SNPS","CDNS","PAYX","MCHP","KLAC","AMAT","NXPI",
    "MMM","AXP","BA","DIS","DOW","NKE","TRV","VZ","WBA","MU",
    # NASDAQ teknoloji
    "ABNB","ADSK","ALGN","ANSS","ATVI","BIDU","BMRN","CMCSA","CPRT","CSGP",
    "CTAS","CTSH","DDOG","DLTR","DOCU","DXCM","EA","EBAY","ENPH","FAST",
    "FISV","IDXX","ILMN","INTC","JD","KDP","LULU","MAR","MELI","MNST",
    "MRNA","MRVL","MTCH","NFLX","NVAX","OKTA","PANW","PCAR","PDD","PYPL",
    "RIVN","ROST","SBUX","SPLK","SWKS","TEAM","TMUS","TTWO","VRSK","VRSN",
    "WDAY","WDC","ZM","ZS","HUBS","SNOW","PLTR","RBLX","COIN","AFRM",
    "UPST","SOFI","HOOD","LCID","DKNG","FUTU","GRAB","SGEN","BIIB","REGN",
    # NYSE büyük şirketler
    "T","VZ","CMCSA","CHTR","NFLX","DIS","PARA","WBD","FOX","FOXA",
    "LMT","RTX","NOC","GD","BA","TDG","HII","L3T","LDOS","SAIC",
    "CVS","WBA","MCK","ABC","CAH","HCA","THC","UHS","CNC","MOH",
    "XOM","CVX","COP","EOG","PXD","DVN","FANG","MRO","APA","OXY",
    "NEE","DUK","SO","D","EXC","SRE","AEP","XEL","WEC","ES",
    "JPM","BAC","WFC","C","GS","MS","BK","STT","USB","PNC",
    "CB","AON","MMC","AIG","MET","PRU","AFL","ALL","TRV","HIG",
    "AMT","PLD","EQIX","CCI","SBAC","DLR","PSA","EXR","AVB","EQR",
    "SPG","O","NNN","WELL","VTR","PEAK","ARE","BXP","SLG","KIM",
    "DE","CAT","CMI","PCAR","ROK","EMR","HON","GE","ETN","ITW",
    "NUE","STLD","CLF","X","AA","FCX","NEM","AEM","GOLD","KGC",
    "LIN","APD","ECL","PPG","SHW","RPM","IFF","ALB","FMC","CE",
    "UNP","CSX","NSC","UPS","FDX","JBHT","CHRW","XPO","ODFL","SAIA",
    "AMZN","WMT","TGT","COST","HD","LOW","BBY","DG","DLTR","FIVE",
    "MCD","SBUX","YUM","QSR","DPZ","CMG","DENN","JACK","TXRH","WING",
    "PFE","JNJ","ABBV","MRK","BMY","AMGN","GILD","REGN","VRTX","BIIB",
    "AAPL","MSFT","GOOGL","META","NVDA","AMD","INTC","QCOM","AVGO","TXN",
    "V","MA","PYPL","SQ","AFRM","SOFI","NU","STNE","GPN","FIS",
    "CRM","ORCL","SAP","NOW","WDAY","ADBE","INTU","CTSH","ACN","IBM",
    "TSLA","GM","F","RIVN","LCID","NIO","LI","XPEV","FSR","RIDE",
]

# ─────────────────────────────────────────────
# KRİPTO
# ─────────────────────────────────────────────
KRIPTO = [
    "BTC-USD","ETH-USD","BNB-USD","XRP-USD","SOL-USD","ADA-USD","DOGE-USD",
    "TRX-USD","DOT-USD","MATIC-USD","LTC-USD","SHIB-USD","AVAX-USD","UNI-USD",
    "LINK-USD","ATOM-USD","XLM-USD","ETC-USD","BCH-USD","APT-USD","FIL-USD",
    "NEAR-USD","ICP-USD","VET-USD","HBAR-USD","QNT-USD","ALGO-USD","GRT-USD",
    "EGLD-USD","AAVE-USD","XMR-USD","EOS-USD","SAND-USD","MANA-USD","AXS-USD",
    "THETA-USD","FTM-USD","FLOW-USD","STX-USD","XTZ-USD","DASH-USD","COMP-USD",
    "YFI-USD","SNX-USD","SUSHI-USD","1INCH-USD","CAKE-USD","OMG-USD","LRC-USD",
    "RUNE-USD","DYDX-USD","IMX-USD","GALA-USD","LDO-USD","APE-USD","OP-USD",
    "ARB-USD","SUI-USD","SEI-USD","TIA-USD","PYTH-USD","WIF-USD","BONK-USD",
    "PEPE-USD","FLOKI-USD","ORDI-USD","LUNC-USD","RAY-USD","DGB-USD","RVN-USD",
    "MASK-USD","ROSE-USD","WBTC-USD","SCRT-USD","INJ-USD","FET-USD","RNDR-USD",
    "OCEAN-USD","AGI-USD","WLD-USD","CFG-USD","HOOK-USD","HIGH-USD","ACH-USD",
]

TUM_HISSELER = list(dict.fromkeys(BIST + ABD + KRIPTO))

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
        denom = (high_[i] - low_[i])
        raw   = 0.66 * ((hl2[i] - low_[i]) / denom - 0.5) + 0.67 * val[i-1] if denom != 0 else 0.67 * val[i-1]
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

def crossover_bars_ago(a, b, max_bars=MAX_BARS):
    for i in range(max_bars + 1):
        idx = -1 - i
        if len(a) < abs(idx) + 1:
            return None
        if a[idx] > b[idx] and a[idx-1] <= b[idx-1]:
            return i
    return None

# ─────────────────────────────────────────────
# VERİ ÇEK
# ─────────────────────────────────────────────
def veri_cek(ticker, deneme=0):
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False, auto_adjust=True)
        if df is None or len(df) < 50:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).capitalize() for c in df.columns]
        df = df.resample("4h").agg({
            "Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"
        }).dropna()
        if len(df) < 50:
            return None
        return df
    except Exception as e:
        hata = str(e)
        if "rate" in hata.lower() or "429" in hata or "too many" in hata.lower():
            if deneme < RETRY:
                time.sleep(10 * (deneme + 1))
                return veri_cek(ticker, deneme + 1)
        return None

# ─────────────────────────────────────────────
# HACİM FİLTRESİ
# ─────────────────────────────────────────────
def hacim_gecti(ticker, df):
    try:
        # Son 3 günün ortalama hacmi (4h mumlardan hesapla)
        son3gun = df.tail(18)  # 3 gün × 6 mum = 18 mum
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
# HİSSE TARA
# ─────────────────────────────────────────────
def hisse_tara(ticker):
    try:
        df = veri_cek(ticker)
        if df is None:
            return False

        # Hacim filtresi
        if not hacim_gecti(ticker, df):
            return False

        close = df["Close"].values.astype(float)
        high  = df["High"].values.astype(float)
        low   = df["Low"].values.astype(float)

        # 1) FISHER
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return False

        # 2) ALMA 4/9
        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False

        # 3) RSI
        rsi_vals = rsi_hesapla(close, 14)
        rsi_sma  = pd.Series(rsi_vals).rolling(14).mean().values
        rsi_bars = crossover_bars_ago(rsi_vals, rsi_sma)
        if rsi_bars is None or rsi_vals[-1] > RSI_MAX:
            return False

        # 4) NW ENVELOPE alt %10
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
def tara():
    print(f"\n[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] Tarama başladı — {len(TUM_HISSELER)} sembol")
    bulunanlar = []

    for i, ticker in enumerate(TUM_HISSELER):
        print(f"  [{i+1}/{len(TUM_HISSELER)}] {ticker}", end=" ", flush=True)
        if hisse_tara(ticker):
            print("✓ SİNYAL")
            bulunanlar.append(ticker)
        else:
            print("✗")
        time.sleep(BEKLEME)

    if bulunanlar:
        mesaj = "🟢 <b>AL Sinyali!</b>\n\n"
        mesaj += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        mesaj += f"📊 Zaman Dilimi: 4 Saatlik\n\n"
        mesaj += "<b>Hisseler:</b>\n"
        for h in bulunanlar:
            temiz = h.replace(".IS","").replace("-USD"," 🪙")
            mesaj += f"  • {temiz}\n"
        mesaj += "\n✅ Fisher + ALMA 4/9 + RSI ≤40 + NW Envelope %10"
        telegram_gonder(mesaj)
        print(f"\n✅ Telegram gönderildi: {bulunanlar}")
    else:
        print("\nSinyal bulunamadı.")

# ─────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    telegram_gonder(
        "🤖 <b>Sinyal Botu Başlatıldı!</b>\n\n"
        "📊 BIST + NYSE + NASDAQ + Kripto\n"
        "⏰ Sürekli tarama (4 saatlik mum)\n\n"
        "Filtreler:\n"
        "• Fisher crossover (2 mum, 0 altı)\n"
        "• ALMA 4/9 crossover (2 mum)\n"
        "• RSI ≤ 40\n"
        "• NW Envelope alt %10\n"
        "• Hacim: son 3 gün ortalaması"
    )
    while True:
        tara()
        print("\n4 saat bekleniyor...")
        time.sleep(4 * 60 * 60)
