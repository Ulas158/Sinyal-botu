import os
import time
import random
import requests
import pandas as pd
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID", "7116490869")

# Tüm olası BIST sembolleri
TUM_BIST = [
    "AEFES","AGESA","AGHOL","AGROT","AHGAZ","AKENR","AKBNK","AKFEN","AKGRT",
    "AKSA","AKSEN","AKSGY","ALARK","ALBRK","ALFAS","ALGYO","ALKIM","ALTIN",
    "ALTNY","ANACM","ANELE","ANGEN","ANHYT","ANSGR","ARASE","ARCLK","ARSAN",
    "ASELS","ASTOR","ATAKP","ATEKS","ATLAS","AYEN","AYCES","AYGAZ","AZTEK",
    "BAGFS","BALSU","BASGZ","BAYRK","BERA","BFREN","BIENY","BIGCH","BIOEN",
    "BIZIM","BJKAS","BLCYT","BMEKS","BNTAS","BOBET","BORSK","BOSSA","BRISA",
    "BRKSN","BRLSM","BRMEN","BRSAN","BSOKE","BTCIM","BUCIM","BURCE","BURVA",
    "BVSAN","CANTE","CASA","CCOLA","CELHA","CEMAS","CEMTS","CEOEM","CIMSA",
    "CLEBI","CMBTN","CMENT","COKAS","COSMO","CRFSA","CUSAN","CVKMD","CWENE",
    "DAGHL","DAGI","DAPGM","DARDL","DENGE","DERIM","DESA","DESPC","DEVA",
    "DGATE","DGNMO","DIRIT","DITAS","DJIST","DMSAS","DNISI","DOAS","DOBUR",
    "DOCO","DOGUB","DOHOL","DOKTA","DURDO","DYOBY","DZGYO","ECILC","ECZYT",
    "EDIP","EFOR","EFORC","EGEEN","EGEPO","EGGUB","EGPRO","EGSER","EKGYO",
    "ENERY","ENJSA","ENKAI","ENSRI","EPLAS","ERBOS","ERCB","EREGL","ERSU",
    "ESCAR","ESCOM","ESEN","ETILR","ETYAT","EUHOL","EUPWR","EUREN","EUYO",
    "EVCIL","FADE","FENER","FFKRL","FMIZP","FONET","FORMT","FORTE","FRIGO",
    "FROTO","GARFA","GARAN","GEDIK","GEDZA","GENIL","GENTS","GEREL","GESAN",
    "GLBMD","GLCVY","GLRMK","GLRYH","GLYHO","GMTAS","GNPWR","GOKNR","GOLTS",
    "GOODY","GOZDE","GRSEL","GRTHO","GSDDE","GSDHO","GSRAY","GUBRF","GWIND",
    "GZNMI","HALKB","HATEK","HDFGS","HEDEF","HEKTS","HKTM","HLGYO","HOROZ",
    "HUBVC","HUNER","HURGZ","ICBCT","ICUGS","INDES","INFO","INTEM","INVEO",
    "IPEKE","ISATR","ISBIR","ISBTR","ISFIN","ISGYO","ISGSY","ISKPL","ISCTR",
    "ISMEN","ISYAT","ITTFK","IZFAS","IZINV","IZMDC","IZENR","JANTS","KAPLM",
    "KARTN","KARSN","KATMR","KAYSE","KCAER","KENT","KERVT","KFEIN","KGYO",
    "KCHOL","KLGYO","KLKIM","KLNMA","KLRHO","KLSYN","KMPUR","KNFRT","KOCMT",
    "KONYA","KONTR","KOPOL","KOZAL","KRDMA","KRDMB","KRDMD","KRPLS","KRSTL",
    "KRTEK","KTLEV","KUYAS","KUTPO","LIDER","LILAK","LKMNH","LRSHO","LUKSK",
    "LOGO","MAALT","MACKO","MAGEN","MARTI","MAVI","MAZGL","MEDTR","MEGAP",
    "MEKAG","MERCN","MERIT","MERKO","METRO","MGROS","MIATK","MIPAZ","MNDRS",
    "MNDTR","MOBTL","MOGAN","MPARK","MSGYO","MTRKS","MZHLD","NATEN","NETAS",
    "NIBAS","NTTUR","NUHCM","OBASE","OBAMS","ODAS","ODEYO","ONCSM","ORCAY",
    "ORGE","OSMEN","OSTIM","OTKAR","OTTO","OYAKC","OYAYO","OYLUM","OZGYO",
    "OZKGY","OZRDN","OZSUB","PAGYO","PAHOL","PAMEL","PAPIL","PARSN","PASEU",
    "PATEK","PCILT","PEGYO","PEKMT","PENGD","PENTA","PETKM","PETUN","PGSUS",
    "PINSU","PKART","PKENT","PLTUR","PNLSN","POLHO","POLTK","PRZMA","PSDTC",
    "PSGYO","PTOFS","QUAGR","RALYH","RAYSG","REEDR","RNPOL","RODRG","ROYAL",
    "RTALB","RUBNS","RYGYO","SAFKR","SAHOL","SANEL","SANFM","SANKO","SARKY",
    "SASA","SAYAS","SDTTR","SEGYO","SEKFK","SEKUR","SELEC","SELGD","SELVA",
    "SEYKM","SILVR","SISE","SKBNK","SNGYO","SNKRN","SNPAM","SODSN","SOKM",
    "SRVGY","SSTEK","STGYO","SUWEN","TABGD","TATGD","TATEN","TATPD","TBORG",
    "TAVHL","TCELL","TDGYO","TEKTU","TERA","TEZOL","TGSAS","THYAO","TKFEN",
    "TKNSA","TLMAN","TMPOL","TNZTP","TOASO","TRALT","TRCAS","TRENJ","TRMET",
    "TRILC","TSGYO","TSPOR","TSKB","TTKOM","TTRAK","TUCLK","TUKAS","TUPRS",
    "TUREX","TURSG","UFUK","ULUUN","UMPAS","ULKER","UNLU","USAK","USDTR",
    "UTPYA","UZERB","VAKBN","VANGD","VBTYZ","VERUS","VESTL","VIBSX","VKFYO",
    "VKGYO","VKING","YAPRK","YATAS","YBTAS","YEOTK","YESIL","YGYO","YGGYO",
    "YKBNK","YKSLN","YUNSA","YYAPI","ZEDUR","ZOREN",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def veri_var_mi(sembol):
    try:
        ticker = sembol + ".IS"
        session = requests.Session()
        session.headers.update(get_headers())
        try:
            session.get("https://fc.yahoo.com", timeout=5)
        except:
            pass
        try:
            crumb = session.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=5).text
        except:
            crumb = ""

        end   = int(time.time())
        start = end - 30 * 24 * 3600

        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            f"?period1={start}&period2={end}&interval=1h&crumb={crumb}"
        )
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return False

        data  = r.json()
        chart = data.get("chart", {}).get("result", [])
        if not chart:
            return False

        timestamps = chart[0].get("timestamp", [])
        return len(timestamps) > 50

    except:
        return False

# ─────────────────────────────────────────────
# TARA
# ─────────────────────────────────────────────
print(f"Test başlıyor — {len(TUM_BIST)} sembol deneniyor")
telegram_gonder(f"🔍 BIST test başladı — {len(TUM_BIST)} sembol deneniyor...")

calisanlar = []
calismayalar = []

for i, sembol in enumerate(TUM_BIST):
    print(f"[{i+1}/{len(TUM_BIST)}] {sembol}", end=" ", flush=True)
    if veri_var_mi(sembol):
        print("✓")
        calisanlar.append(sembol)
    else:
        print("✗")
        calismayalar.append(sembol)
    time.sleep(random.uniform(2, 4))

# Sonucu Telegram'a gönder
mesaj = f"✅ <b>BIST Test Tamamlandı!</b>\n\n"
mesaj += f"📊 Toplam denenen: {len(TUM_BIST)}\n"
mesaj += f"✓ Veri var: {len(calisanlar)}\n"
mesaj += f"✗ Veri yok: {len(calismayalar)}\n\n"
mesaj += f"<b>Çalışan hisseler:</b>\n"
mesaj += ", ".join(calisanlar)

# Mesaj çok uzunsa böl
if len(mesaj) > 4000:
    parca1 = mesaj[:4000]
    parca2 = "📋 <b>Devam:</b>\n" + ", ".join(calisanlar[100:])
    telegram_gonder(parca1)
    time.sleep(1)
    telegram_gonder(parca2)
else:
    telegram_gonder(mesaj)

print(f"\nSonuç: {len(calisanlar)} hissede veri var")
print("Çalışanlar:", calisanlar)
