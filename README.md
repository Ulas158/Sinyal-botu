# Kombine AL Sinyal Botu

## Railway Kurulum Adımları

### 1. GitHub'a yükle
1. github.com'a git, hesap aç (ücretsiz)
2. "New repository" → isim ver (örn: `sinyal-botu`) → Create
3. Dosyaları yükle: main.py, requirements.txt, railway.toml

### 2. Railway kurulumu
1. railway.app'e git → GitHub ile giriş yap
2. "New Project" → "Deploy from GitHub repo"
3. Repo'nu seç

### 3. Environment Variables ekle
Railway'de projeye gir → "Variables" sekmesi → şunları ekle:

```
TELEGRAM_TOKEN = <yeni telegram tokenin>
CHAT_ID        = 7116490869
```

### 4. Deploy et
"Deploy" butonuna bas — bot başlayacak ve Telegram'a mesaj atacak.

---

## Bot Ne Zaman Sinyal Atar?

Her 4 saatte bir 100 hisseyi tarar. Şu 4 koşulun hepsi sağlandığında AL sinyali atar:

1. **Fisher Transform**: Mavi çizgi kırmızıyı yukarı kestiyse ve 0'ın altındaysa (son 3 mumda)
2. **ALMA 4/9**: ALMA4, ALMA9'u yukarı kestiyse (son 3 mumda)
3. **RSI**: RSI, SMA'sını yukarı kestiyse ve RSI ≤ 50 ise (son 3 mumda)
4. **NW Envelope**: Fiyat alt bandın alt %30'unda ise

## Ücret
Railway ücretsiz tier: ayda 500 saat → bu bot için yeterli.
