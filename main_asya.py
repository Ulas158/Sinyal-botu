import os
import time
import random
import requests
import numpy as np
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID        = os.environ.get("CHAT_ID", "7116490869")
GITHUB_USER    = os.environ.get("GITHUB_USER", "Ulas158")
MAX_BARS       = 2
RSI_MAX        = 40.0
NW_ZONE        = 0.10
RETRY          = 3
BEKLEME_MIN    = 3.0
BEKLEME_MAX    = 6.0
JAPONYA_HACIM  = 750_000_000  # ~5M USD yen bazında
HONGKONG_HACIM = 5_000_000
ALMANYA_HACIM  = 5_000_000

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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

# ─────────────────────────────────────────────
# JAPONYA — Prime Market hisseleri
# ─────────────────────────────────────────────
JAPONYA_LISTE = [
    "1301","1332","1333","1377","1379","1414","1430","1433","1434","1435",
    "1436","1437","1438","1439","1440","1441","1442","1443","1444","1445",
    "1446","1447","1448","1449","1450","1451","1452","1453","1454","1455",
    "1456","1457","1458","1459","1460","1461","1462","1463","1464","1465",
    "1467","1468","1469","1470","1471","1472","1473","1474","1475","1476",
    "1477","1478","1479","1480","1481","1482","1483","1484","1485","1486",
    "1488","1489","1490","1491","1492","1493","1494","1495","1496","1497",
    "1498","1499","1500","1501","1502","1503","1504","1505","1506","1507",
    "1508","1509","1510","1511","1512","1513","1514","1515","1516","1517",
    "1518","1519","1520","1521","1522","1523","1524","1525","1526","1527",
    "1605","1662","1663","1667","1668","1669","1670","1671","1672","1675",
    "1712","1721","1722","1723","1724","1725","1726","1727","1728","1729",
    "1730","1731","1732","1733","1734","1735","1736","1737","1738","1739",
    "1740","1741","1742","1743","1744","1745","1746","1747","1748","1749",
    "1750","1751","1752","1753","1754","1755","1756","1757","1758","1759",
    "1760","1761","1762","1763","1764","1765","1766","1767","1768","1769",
    "1770","1771","1772","1773","1774","1775","1776","1777","1778","1779",
    "1780","1781","1782","1783","1784","1785","1786","1787","1788","1789",
    "1790","1791","1792","1793","1794","1795","1796","1797","1798","1799",
    "1801","1802","1803","1804","1805","1806","1807","1808","1809","1810",
    "1811","1812","1813","1814","1815","1816","1817","1818","1819","1820",
    "1821","1822","1823","1824","1825","1826","1827","1828","1829","1830",
    "1833","1835","1840","1841","1844","1847","1848","1850","1852","1853",
    "1860","1861","1862","1863","1864","1865","1866","1867","1868","1869",
    "1870","1871","1872","1873","1874","1875","1876","1877","1878","1879",
    "1880","1881","1882","1883","1884","1885","1886","1887","1888","1889",
    "1890","1891","1892","1893","1894","1895","1896","1897","1898","1899",
    "1900","1901","1902","1903","1904","1905","1906","1907","1908","1909",
    "1911","1912","1913","1914","1915","1916","1917","1918","1919","1920",
    "1921","1922","1923","1924","1925","1926","1927","1928","1929","1930",
    "1931","1932","1933","1934","1935","1936","1937","1938","1939","1940",
    "1941","1942","1943","1944","1945","1946","1947","1948","1949","1950",
    "1951","1952","1953","1954","1955","1956","1957","1958","1959","1960",
    "1961","1962","1963","1964","1965","1966","1967","1968","1969","1970",
    "1971","1972","1973","1974","1975","1976","1977","1978","1979","1980",
    "1981","1982","1983","1984","1985","1986","1987","1988","1989","1990",
    "1991","1992","1993","1994","1995","1996","1997","1998","1999","2001",
    "2002","2003","2004","2005","2006","2007","2008","2009","2010","2011",
    "2012","2013","2014","2015","2016","2017","2018","2019","2020","2021",
    "2022","2023","2024","2025","2026","2027","2028","2029","2030","2031",
    "2109","2114","2117","2124","2127","2130","2131","2132","2133","2134",
    "2201","2202","2206","2207","2208","2209","2211","2212","2213","2215",
    "2216","2217","2220","2221","2222","2224","2225","2226","2228","2229",
    "2230","2231","2233","2235","2237","2238","2239","2240","2241","2242",
    "2243","2244","2245","2246","2247","2248","2249","2250","2251","2252",
    "2253","2261","2262","2264","2265","2266","2267","2268","2269","2270",
    "2271","2272","2274","2275","2276","2281","2282","2283","2284","2285",
    "2286","2287","2288","2289","2291","2292","2293","2296","2297","2298",
    "2301","2303","2305","2307","2308","2309","2310","2311","2312","2313",
    "2315","2317","2318","2319","2321","2323","2325","2327","2329","2330",
]

def japonya_listesi_cek():
    # FinanceDataReader ile TSE listesi çek
    try:
        print("Japonya listesi çekiliyor (FinanceDataReader)...")
        import FinanceDataReader as fdr
        df = fdr.StockListing("TSE")
        semboller = [str(s).strip() + ".T" for s in df["Symbol"].dropna().tolist() if str(s).strip()]
        semboller = list(dict.fromkeys(semboller))
        semboller = semboller[:1500]  # top 1500
        if len(semboller) >= 100:
            print(f"Japonya (TSE): {len(semboller)} hisse")
            return semboller
        raise Exception(f"Yeterli sembol yok: {len(semboller)}")
    except Exception as e:
        print(f"FinanceDataReader TSE hatası: {e}")
        print(f"Japonya sabit liste: {len(JAPONYA_LISTE)} hisse")
        return [k + ".T" for k in JAPONYA_LISTE]

# ─────────────────────────────────────────────
# HONG KONG — HKEX hisseleri
# ─────────────────────────────────────────────
HONGKONG_LISTE = [
    "0001","0002","0003","0004","0005","0006","0007","0008","0009","0010",
    "0011","0012","0013","0014","0015","0016","0017","0018","0019","0020",
    "0023","0027","0066","0083","0087","0101","0135","0138","0144","0151",
    "0175","0241","0256","0257","0267","0285","0288","0291","0358","0371",
    "0386","0388","0522","0570","0656","0659","0669","0688","0700","0762",
    "0823","0836","0857","0868","0883","0914","0939","0941","0960","0992",
    "1024","1038","1044","1093","1109","1113","1171","1177","1199","1288",
    "1299","1308","1357","1378","1398","1810","1876","1918","1928","1997",
    "2007","2018","2020","2313","2318","2319","2382","2388","2628","2800",
    "3328","3618","3690","3988","6098","6618","6837","6862","9888","9999",
    "0021","0022","0024","0025","0026","0028","0029","0030","0031","0032",
    "0033","0034","0035","0036","0037","0038","0039","0040","0041","0042",
    "0043","0044","0045","0046","0047","0048","0049","0050","0051","0052",
    "0053","0054","0055","0056","0057","0058","0059","0060","0061","0062",
    "0063","0064","0065","0067","0068","0069","0070","0071","0072","0073",
    "0074","0075","0076","0077","0078","0079","0080","0081","0082","0084",
    "0085","0086","0088","0089","0090","0091","0092","0093","0094","0095",
    "0096","0097","0098","0099","0100","0102","0103","0104","0105","0106",
    "0107","0108","0109","0110","0111","0112","0113","0114","0115","0116",
    "0117","0118","0119","0120","0121","0122","0123","0124","0125","0126",
    "0127","0128","0129","0130","0131","0132","0133","0134","0136","0137",
    "0139","0140","0141","0142","0143","0145","0146","0147","0148","0149",
    "0150","0152","0153","0154","0155","0156","0157","0158","0159","0160",
    "0161","0162","0163","0164","0165","0166","0167","0168","0169","0170",
    "0171","0172","0173","0174","0176","0177","0178","0179","0180","0181",
    "0182","0183","0184","0185","0186","0187","0188","0189","0190","0191",
    "0192","0193","0194","0195","0196","0197","0198","0199","0200","0201",
    "0202","0203","0204","0205","0206","0207","0208","0209","0210","0211",
    "0212","0213","0214","0215","0216","0217","0218","0219","0220","0221",
    "0222","0223","0224","0225","0226","0227","0228","0229","0230","0231",
    "0232","0233","0234","0235","0236","0237","0238","0239","0240","0242",
    "0243","0244","0245","0246","0247","0248","0249","0250","0251","0252",
    "0253","0254","0255","0258","0259","0260","0261","0262","0263","0264",
    "0265","0266","0268","0269","0270","0271","0272","0273","0274","0275",
    "0276","0277","0278","0279","0280","0281","0282","0283","0284","0286",
    "0287","0289","0290","0292","0293","0294","0295","0296","0297","0298",
    "0299","0300","0301","0302","0303","0304","0305","0306","0307","0308",
    "0309","0310","0311","0312","0313","0314","0315","0316","0317","0318",
    "0319","0320","0321","0322","0323","0324","0325","0326","0327","0328",
    "0329","0330","0331","0332","0333","0334","0335","0336","0337","0338",
    "0339","0340","0341","0342","0343","0344","0345","0346","0347","0348",
    "0349","0350","0351","0352","0353","0354","0355","0356","0357","0359",
    "0360","0361","0362","0363","0364","0365","0366","0367","0368","0369",
    "0370","0372","0373","0374","0375","0376","0377","0378","0379","0380",
    "0381","0382","0383","0384","0385","0387","0389","0390","0391","0392",
    "0393","0394","0395","0396","0397","0398","0399","0400","0401","0402",
    "0403","0404","0405","0406","0407","0408","0409","0410","0411","0412",
    "0413","0414","0415","0416","0417","0418","0419","0420","0421","0422",
    "0423","0424","0425","0426","0427","0428","0429","0430","0431","0432",
    "0433","0434","0435","0436","0437","0438","0439","0440","0441","0442",
    "0443","0444","0445","0446","0447","0448","0449","0450","0451","0452",
]

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
        sonuc = sonuc[:1500]  # top 1500
        if len(sonuc) >= 50:
            print(f"Hong Kong (HKEX): {len(sonuc)} hisse")
            return sonuc
        raise Exception(f"Yeterli sembol yok: {len(sonuc)}")
    except Exception as e:
        print(f"FinanceDataReader HKEX hatası: {e}")
        print(f"Hong Kong sabit liste: {len(HONGKONG_LISTE)} hisse")
        return [k + ".HK" for k in HONGKONG_LISTE]

# ─────────────────────────────────────────────
# ALMANYA — Frankfurt Borsası
# ─────────────────────────────────────────────
ALMANYA_LISTE = [
    # DAX 40
    "SAP","AIR","ADS","ALV","MUV2","DTE","RWE","SIE","BMW","MBG",
    "DBK","DPW","HEI","VOW3","BAS","BAYN","ENR","FRE","HEN3","IFX",
    "MRK","PUM","QIA","RHM","SHL","SY1","VNA","ZAL","1COV","BNR",
    "CON","P911","HNR1","DHER","DWS","FME","HLAG","IONOS","MBB","MTX",
    # MDAX
    "AFX","AG1","AIXA","BOSS","CARL","COK","COP","EVD","GFK","HFG",
    "HOT","JEN","KGX","LEG","LHA","LXS","MDO","NDX1","NEM","O2D",
    "PAH3","PBB","SDF","SFQ","SGL","SKB","SMHN","SZG","TLX","TUI1",
    "VBK","WAF","VOS","VIB3","UTDI","TEG","TDT","SW","FNTN","GBF",
    "KSB3","OSR","SOW","STO3","TBO","TPVG","EVT","CARL","MXHN","NGLB",
    # SDAX
    "SRT3","SLT","SIX2","SIS","RAA","RKET","PSM","PRG","NOEJ","NDA",
    "MVOB","MOR","MNX","MLP","KION","KD8","JUN3","IVU","ISRA","HHFA",
    "HDD","HAB","GXI","GWI","GAM","ERF","DEQ","DAR","CWC","CUE",
    "CIO","CEC","CBK","CAP","BYW6","BVB","BAF","AT1","ARL","APN",
    "AMO","ADV","ACX","ACT","TUI","AAD","WDI","LEO","KWS","EVO",
    # TecDAX
    "NDA","NDX1","PSM","QIA","SGL","SIS","SLT","SRT3","TEG","TLX",
    "UTDI","VBK","WAF","ZAL","SOW","DWS","FNTN","AIXA","IFX","JEN",
]

def almanya_listesi_cek():
    # Plan A: FinanceDataReader ETR
    try:
        print("Almanya listesi çekiliyor (FinanceDataReader ETR)...")
        import FinanceDataReader as fdr
        df = fdr.StockListing("ETR")
        semboller = [str(s).strip() + ".DE" for s in df["Symbol"].dropna().tolist() if str(s).strip()]
        semboller = list(dict.fromkeys(semboller))
        if len(semboller) >= 50:
            print(f"Almanya (ETR): {len(semboller)} hisse")
            return semboller
        raise Exception(f"Yeterli sembol yok: {len(semboller)}")
    except Exception as e:
        print(f"FinanceDataReader ETR hatası: {e}")

    # Plan B: Deutsche Börse Xetra resmi listesi
    try:
        print("Almanya listesi çekiliyor (Xetra)...")
        url = "https://stockanalysis.com/list/deutsche-boerse-xetra/"
        headers = get_headers()
        headers["Accept"] = "application/json, text/plain, */*"
        r = requests.get(url, headers=headers, timeout=20)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        semboller = []
        # Tablodaki semboller
        for td in soup.find_all("td"):
            a = td.find("a")
            if a and "/stocks/" in a.get("href",""):
                sembol = a.text.strip().upper()
                if sembol and 1 <= len(sembol) <= 6:
                    semboller.append(sembol + ".DE")
        semboller = list(dict.fromkeys(semboller))
        if len(semboller) >= 50:
            print(f"Almanya (Xetra): {len(semboller)} hisse")
            return semboller
        raise Exception(f"Yeterli sembol yok: {len(semboller)}")
    except Exception as e:
        print(f"Xetra hatası: {e}")

    # Plan C: Sabit liste
    semboller = list(dict.fromkeys([s + ".DE" for s in ALMANYA_LISTE]))
    print(f"Almanya sabit liste: {len(semboller)} hisse")
    return semboller

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
            return ort_hacim >= JAPONYA_HACIM
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

        # 1) FISHER — yukarı kesişim + ters kırılım yok
        fish1, fish2 = fisher_transform(high, low, 9)
        fisher_bars  = crossover_bars_ago(fish1, fish2)
        if fisher_bars is None or fish1[-1 - fisher_bars] >= 0:
            return False
        for i in range(fisher_bars - 1, -1, -1):
            if fish1[-1 - i] < fish2[-1 - i]:
                return False

        # 2) ALMA 4/9 — yukarı kesişim + ters kırılım yok
        alma4     = alma(close, 4)
        alma9     = alma(close, 9)
        alma_bars = crossover_bars_ago(alma4, alma9)
        if alma_bars is None:
            return False
        for i in range(alma_bars - 1, -1, -1):
            if alma4[-1 - i] < alma9[-1 - i]:
                return False

        # 3) RSI — yukarı kesişim + ters kırılım yok
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
        f"• NW Envelope alt %10"
    )

    while True:
        jp_listesi = japonya_listesi_cek()
        hk_listesi = hongkong_listesi_cek()
        de_listesi = almanya_listesi_cek()
        tum_liste  = list(dict.fromkeys(jp_listesi + hk_listesi + de_listesi))
        tara(tum_liste)
        print("\nYeni tur başlıyor...\n")
