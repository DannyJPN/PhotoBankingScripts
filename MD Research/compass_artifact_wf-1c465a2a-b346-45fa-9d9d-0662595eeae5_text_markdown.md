# Automatická detekce veřejné dostupnosti fotografií na fotobankách

Nejspolehlivější cestou k ověření, zda je konkrétní fotografie veřejně živá na customer-facing webu fotobanky, je **kombinace oficiálního API (kde existuje) s perceptuálním hashováním preview obrázků**. Ze zkoumaných 18 fotobank nabízí použitelné API jen 7–8 z nich, přičemž pouze Shutterstock, Adobe Stock a Freepik poskytují self-service přístup bez nutnosti obchodního jednání. Zbývající banky vyžadují buď partnerský vztah, nebo se spoléhají na scraping veřejného webu — přístup technicky proveditelný, ale provozně křehký kvůli anti-bot ochranám. CanStockPhoto ukončil provoz v říjnu 2023 a je irelevantní. Klíčové zjištění: **žádná univerzální metoda nefunguje spolehlivě napříč všemi bankami** — nutný je bank-specific adapter pattern s víceúrovňovým ověřením.

---

## Srovnávací tabulka všech fotobank

| Banka | Bez loginu? | S contrib. loginem? | API? | Veřejné search? | Portfolio? | Preview dostupné? | Primární přístup | Riziko FP | Riziko FN | Priorita |
|-------|------------|---------------------|------|-----------------|-----------|-------------------|-----------------|-----------|-----------|----------|
| **Shutterstock** | ✅ | ✅ | ✅ Self-serve (omezené) | ✅ (JS) | ✅ `/g/USER` | ✅ (CDN) | API + portfolio scrape | Nízké | Střední (free API = omezená knihovna) | **Tier 1** |
| **Adobe Stock** | ✅ | ✅ | ⚠️ Nově omezené (Enterprise/Affiliate) | ✅ (JS) | ✅ `/contributor/{id}` | ✅ ftcdn.net | API (Files endpoint) | Nízké | Nízké (API = source of truth) | **Tier 1** |
| **Getty/iStock** | ✅ | N/A | ⚠️ Pouze přes obch. oddělení | ✅ (JS) | ❌ Slabé | ✅ media.gettyimages.com | API (pokud dostupné) / web | Nízké | Střední | **Tier 2** |
| **DepositPhotos** | ✅ | ✅ | ✅ (registrace) | ✅ | ✅ `/portfolio-{id}` | ✅ static.depositphotos.com | API `getMediaData` | Nízké | Nízké | **Tier 1** |
| **123RF** | ✅ | ✅ | ✅ Zdarma (non-commercial) | ✅ | ✅ `/profile_{id}` | ✅ us-cdn.123rf.com | API `getInfo` | Nízké | Nízké | **Tier 1** |
| **Pond5** | ✅ | ✅ | ⚠️ Enterprise-only | ✅ (403 bot) | ✅ `/artist/USER` | ✅ ec.pond5.com | CDN check + `get_clip_data` | Nízké | Střední (API stav nejistý) | **Tier 2** |
| **Dreamstime** | ✅ | ✅ | ⚠️ Vyžaduje schválení | ✅ | ✅ `/USER_info` | ✅ thumbs.dreamstime.com | Web search + reverse image | Střední | Střední | **Tier 2** |
| **BigStockPhoto** | ✅ | ✅ | ✅ Self-serve `/partners` | ✅ | ⚠️ Jen přes filtr | ✅ (Shutterstock CDN) | API | Nízké | Nízké | **Tier 2** |
| **Alamy** | ✅ | ✅ | ⚠️ Partnerství (OAuth) | ✅ (robots.txt blokuje) | ⚠️ Zrušeno 02/2025 | ✅ c7.alamy.com/comp/ | CDN preview check | Nízké | Střední | **Tier 2** |
| **Freepik** | ✅ | ✅ | ✅ Self-serve ($5 kredit zdarma) | ✅ | ✅ `/author/{slug}` | ✅ img.freepik.com | API (Stock Content) | Nízké | Nízké | **Tier 1** |
| **Vecteezy** | ✅ | ✅ | ✅ ($40/měsíc) | ✅ (403 bot) | ✅ `/members/{user}` | ⚠️ (403 na CDN) | API (placené) | Nízké | Střední | **Tier 3** |
| **StoryBlocks** | ✅ | N/A | ⚠️ B2B only | ✅ (SPA) | ❌ | ⚠️ Watermarked | Headless browser | Střední | Střední | **Tier 3** |
| **Envato Elements** | ✅ | ✅ | ⚠️ Jen Market API (ne Elements) | ✅ | ⚠️ | ✅ | Headless + XHR intercept | Střední | Vysoké | **Tier 3** |
| **PIXTA** | ✅ | ✅ | ❌ | ✅ | ⚠️ (vyžaduje URL) | ✅ | Web search (HTTP) | Střední | Střední | **Tier 3** |
| **MostPhotos** | ⚠️ (405) | ? | ❌ | ⚠️ Blokováno | ? | ? | Playwright pouze | Vysoké | Vysoké | **Tier 4** |
| **500px** | ✅ | ✅ | ❌ (zrušeno 2018) | ✅ (JS) | ✅ `/username` | ✅ | Headless + internal API | Střední | Střední | **Tier 3** |
| **CanStockPhoto** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **UKONČEN (10/2023)** | N/A | N/A | **Tier 4** |

---

## Detailní rozbor po jednotlivých bankách

### Shutterstock — solidní API s kritickým omezením free tieru

Shutterstock nabízí **nejlépe dokumentované veřejné API** mezi fotobankami. Base URL je `https://api.shutterstock.com/v2/`, klíčové endpointy zahrnují `/images/search` (29+ parametrů), `/images/{id}` pro detail konkrétního snímku a `/cv/images` + `/cv/similar/images` pro reverse image search. Autentizace vyžaduje minimálně Basic Auth (consumer key + secret), registrace aplikace je self-service na `shutterstock.com/account/developers/apps`.

**Kritické omezení free tieru**: bezplatné API klíče prohledávají pouze **omezenou podmnožinu knihovny** (Free stock photos), nikoli celý katalog. Fotografie přítomná na shutterstock.com se nemusí v API výsledcích free tieru vůbec objevit. Pro spolehlivé ověření celého katalogu je nutná **placená API subscripce**. Rate limit free tieru činí **100 volání/hodinu**, CV endpointy **5 požadavků/minutu**.

Contributor portfolio na `shutterstock.com/g/USERNAME` je **veřejně přístupné bez přihlášení** a bylo úspěšně fetchováno jednoduchým HTTP požadavkem — žádná agresivní anti-bot ochrana. Stránky zobrazují cca **100 obrázků na stránku** s paginací přes `?page=N`, u velkých portfolií existuje 500+ stránek. Každý obrázek obsahuje titulek, thumbnail a odkaz na detail.

URL vzor pro jednotlivé fotografie: `shutterstock.com/image-photo/{SLUG}-{ID}`. Preview obrázky jsou dostupné z více CDN: `image.shutterstock.com` (watermarked 450px+), `thumb1-9.shutterstock.com` (non-watermarked malé thumbnaile), a **260nw thumbnaily** přímo z webu (`image-photo/{SLUG}-260nw-{ID}.jpg`) které nemají Shutterstock watermark. Větší preview (`watermark_1000` na `ak.picdn.net`) obsahují neprediktovatelný hash — nelze konstruovat z ID.

**Doporučená rozhodovací logika**: Pokud je znám asset ID → API `GET /v2/images/{id}` (HTTP 200 = live, 404 = ne). Pokud ID není známé → prohledat contributor portfolio stránky, z nalezených kandidátů stáhnout 260nw thumbnail a porovnat perceptuálním hashem. Reverse image search přes CV endpoint je nejvýkonnější, ale vyžaduje minimálně placený tier.

### Adobe Stock — nejautoritativnější API, ale recentně omezený přístup

Adobe Stock API na `stock.adobe.io` je **technicky nejlepší zdroj pravdy** pro ověření dostupnosti. Endpoint `/Rest/Media/1/Files` přijímá až **110 čárkou oddělených ID** v jednom požadavku a vrací metadata pouze pro existující/živé assety — chybějící ID jsou **tiše vynechány**. Pole `nb_results` udává počet nalezených živých assetů. Adobe explicitně dokumentuje: *„API je vždy aktuální... CDN obrázek může existovat i po stažení assetu z webu."*

Pro vyhledávání stačí hlavičky `x-api-key` + `x-Product` — **OAuth token není nutný** pro search/metadata operace. Klíčové search parametry zahrnují `search_parameters[creator_id]`, `search_parameters[similar_url]` (vizuální podobnost z URL), `search_parameters[similar_image]` (upload obrázku, POST). Adobe Sensei AI pohání jak textové, tak vizuální vyhledávání.

**Závažné omezení (nové)**: API přístup je nyní **omezen na Stock for Enterprise zákazníky a Adobe Affiliates**. Neoprávnění vývojáři musí žádat přes Adobe Prerelease program — schválení není garantováno. Stávající API klíče fungují, ale úpravy vyžadují re-approval.

Thumbnail CDN na `as{1-4}.ftcdn.net` a `t{1-4}.ftcdn.net` servíruje preview ve velikostech 110–1000px. Malé thumbnaily (110–240px) jsou **bez watermarku**, větší (500–1000px) s watermarkem. URL vzor: `https://as{N}.ftcdn.net/v2/jpg/{AA}/{BB}/{CC}/{DD}/{SIZE}_F_{ASSET_ID}_{HASH}.jpg` — hash nelze odvodit z ID, nutné získat z API. Contributor stránky na `stock.adobe.com/contributor/{creator_id}/{name}` jsou veřejně přístupné. Web používá **Akamai CDN** s bot managerem, React SPA vyžadující JS rendering.

### Getty Images a iStock — unifikované API, ale ne self-service

Getty provozuje **jednotné API v3** na `api.gettyimages.com` pokrývající jak Getty Images tak iStock. Endpoint `GET /v3/images/{id}` vrací HTTP 200 s plnou metadatou pro živé assety nebo 404 s `ImageNotFound` pro neexistující. Pole `referral_destinations` uvádí konkrétní customer-facing URL, kde je asset nalezitelný. Endpoint `/v3/artists/images?artist_name={name}` umožňuje filtrování podle fotografa.

**Klíčový problém**: API **není self-service**. Získání API klíče vyžaduje kontakt s obchodním oddělením Getty. Rate limiting je per-key na bázi QPS, konfigurovatelný při registraci. iStock assety se identifikují polem `istock_collection` (essentials/signature).

URL vzory: Getty `gettyimages.com/detail/photo/{slug}/{id}`, iStock `istockphoto.com/photo/{slug}-gm{id}`. Preview na `media.gettyimages.com` s parametry `?s={size}&h={hash}` — thumbnail (170px) a comp (612px) jsou volně přístupné, URL obsahují hash a nejsou permanentní. Oba weby jsou **JavaScript-heavy SPA** na Amazon CloudFront CDN.

Alternativní ověření přes oEmbed: pokud `uri_oembed` endpoint vrátí validní data, asset existuje. Embed feature je dostupná pro nekomerční použití.

### DepositPhotos — dobře strukturované API s přímým stavovým polem

API na `api.depositphotos.com` používá příkazový systém: `dp_command=search` pro vyhledávání, `dp_command=getMediaData` pro detail konkrétního assetu. Response `getMediaData` obsahuje **pole `status: "active"`** — přímé potvrzení, že asset je živý a veřejně dostupný. API klíč se získá registrací na `depositphotos.com/api-program/signup.html`, partnerské a reseller klíče vyžadují individuální žádost.

Veřejné search URL: `depositphotos.com/photos/{keyword}.html`. Web podporuje **filtrování podle contributor jména** přímo ve vyhledávání a nabízí **reverse image search** (upload preview nebo URL přes ikonu kamery). Contributor portfolia na `depositphotos.com/portfolio-{userid}.html` jsou veřejně přístupná.

Thumbnail CDN na `static{N}.depositphotos.com` servíruje watermarked preview volně přístupné bez autentizace. **Nepotřebuje JS rendering** tak agresivně jako Adobe/Getty — backend je PHP s Backbone.js, částečně server-rendered pro SEO.

### 123RF — nejdostupnější bezplatné API pro vyhledávání

API na `www.123rfapis.com` nabízí **bezplatné non-commercial klíče** (žádost na `123rf.com/api/key/apply.php`, schválení ~24 hodin). Pro startupy pod 50K MAU je k dispozici i bezplatné content API. Endpoint `getInfo` s parametrem `id` vrací kompletní metadata: popis, klíčová slova, jméno contributora, dimensions, kategorie. Endpoint `search` podporuje až **100 výsledků na stránku** s paginací do **10 000 stránek**.

URL vzor pro fotografie: `123rf.com/photo_{id}_{slug}.html`. Preview CDN na `us-cdn{1-4}.123rf.com` s vzorem `168nwm/{contributor}/{folder}/{filename}/{id}-{slug}.jpg` — watermarked kompresované náhledy jsou **volně přístupné**. Web je převážně server-rendered, což usnadňuje HTTP scraping oproti SPA bankám. Anti-bot ochrana je **mírná** — žádný Cloudflare Bot Management ani DataDome nebyl identifikován.

### Pond5 — nejistý stav API po akvizici Shutterstockem

Pond5 byl akvizitován Shutterstockem v 2022 za $210M a status jeho API je nejistý. Dokumentace byla naposledy aktualizována v lednu 2018. Příkaz `get_clip_data` historicky **nevyžadoval přihlášení** — POST na `pond5.com/?page=api` s `itemid` vrátil metadata. XML Search endpoint na `pond5.com/document/xml_search.html` rovněž nevyžadoval autentizaci.

Thumbnail CDN na `ec.pond5.com/s3/` má **dokumentovaný a prediktovatelní vzor**: ID se padding na 9 číslic, přípona `_icon.jpeg` (120×66), `_iconm.jpeg` (240×134), `_iconl.jpeg` (480×268), `_prevstill.jpeg` (1280×720). Toto je **nejjednodušší CDN check ze všech bank** — stačí HTTP HEAD request na konstruovanou URL. Web vrací **403** na běžné HTTP požadavky — silná anti-bot ochrana (pravděpodobně Cloudflare).

Pond5 má **patentovanou Visual Search** technologii na `explore.pond5.com/visual-search/`. Primární zaměření je na video, fotky jsou sekundární nabídkou.

### Dreamstime — legacy platforma s reverse image searchem

API na `dreamstime.com/api/` vyžaduje registraci a manuální schválení. WordPress plugin odhalil strukturu: `DreamstimeApi` s `$apiUrl = 'http://www.dreamstime.com/api/'`, session-based autentizace. Veřejné search URL: `dreamstime.com/photos-images/{keyword}.html`. Contributor stránky na `dreamstime.com/{username}_info` jsou veřejné.

**Reverse image search** funguje od prosince 2018 — upload thumbnail najde přesné shody i podobné obrázky. Image detail URL vzor: `dreamstime.com/{slug}-image{numeric_id}`. Je možné vyhledávat přímo podle file ID. Web vrací **403** na přímé fetch požadavky, ale stránky jsou částečně server-rendered (ne čistý SPA), což je lepší pro parsing.

### BigStockPhoto — Shutterstock subsidiary s vlastním API

Vlastněn Shutterstockem od 2009, provozován jako samostatná entita. API na `api.bigstockphoto.com/2/` s OAuth autentizací, self-service registrace na `bigstockphoto.com/partners`. PHP klient (`github.com/shutterstock/bigstock-php-client`) je **deprecated**, což signalizuje potenciální přechod nebo útlum. Veřejné search na `bigstockphoto.com/search/{keyword}/` funguje bez přihlášení s filtrem na contributora. Web vrací **403** na programatické požadavky. TOS explicitně zakazuje automatizovaný přístup k webu — API je doporučená cesta.

### Alamy — CDN preview check jako hlavní metoda

Alamy API vyžaduje **partnerský vztah s OAuth 2.0** (registrace přes `alamy.com/api-partnerships/`). Dokumentace je hostována jako SPA na Stoplight, plné parametry nejsou extrahovatelné bez JS renderování.

**Nejpraktičtější metoda**: CDN preview URL check. Vzor `https://c7.alamy.com/comp/{IMAGE_ID}/{slug}-{IMAGE_ID}.jpg` kde `IMAGE_ID` je 6–7znakový alfanumerický kód (např. `GG409M`). HTTP 200 = asset existuje, 404 = není dostupný. Toto nevyžaduje žádnou autentizaci.

Veřejné search podporuje bohatou sadu parametrů: `qt` (dotaz), `name` (contributor), `id` (image ID), `imageurl` (reverse image search URL), `simid` (similar image ID), `pn`/`ps` (paginace do 100/stránku). Avšak **robots.txt blokuje** automatizované fetchování search výsledků a detail stránek. Portfolio stránky na `alamy.com/portfolio/{name}` byly **pravděpodobně vypnuty v únoru 2025**. Alternativa: search URL s parametrem `plno={contributor_number}`.

**Pozor**: Alamy Image ID (alfanumerický, např. `GG409M`) se liší od numerického ID v URL (např. `104720071`). Pro CDN check potřebujete alfanumerické ID.

### Freepik — nejlepší developer experience

Freepik má **nejpřístupnější moderní API** ze všech zkoumaných bank. REST API na `api.freepik.com/v1/` s dokumentací na `docs.freepik.com/` (Mintlify). Registrace na `freepik.com/developers/dashboard` poskytuje **$5 kredit zdarma**. Autentizace hlavičkou `x-freepik-api-key`.

Stock Content API endpoint `GET /v1/resources` vrací: `id`, `title`, `url` (přímý odkaz na stránku), `filename`, `author.id`, `author.name`, `author.slug`, `stats.downloads`, `meta.published_at`. Parametr `term` pro textové vyhledávání, `slug` pro přímý lookup. Response potvrzuje existenci a veřejnou dostupnost assetu.

CDN preview na `img.freepik.com/free-photo/{slug}_{id}.jpg` (velké preview) a `img.freepik.com/premium-photo/{slug}_{id}.jpg` jsou **volně přístupné**. Autor avatary na `avatar.cdnpk.net/{author_id}.jpg`. Podporuje **Search by Image** (reverse image search). Tech stack založen na Vue.js (pravděpodobně Nuxt.js), ne Next.js.

### Vecteezy — placené API, silná anti-bot ochrana

REST API s interaktivní Swagger dokumentací na `vecteezy.com/api-docs` (vrací 403 botům). Dostupné na RapidAPI od **$40/měsíc**. Supports keyword search, filtry, download. Asset URL vzor: `vecteezy.com/vector-art/{id}-{slug}` (vektory), `vecteezy.com/photo/{id}-{slug}` (fotky). Contributor stránky na `vecteezy.com/members/{username}`. **Silná anti-bot ochrana** — web i API docs vrací 403 programatickým klientům. Původně zaměřen na vektory, fotky od srpna 2020.

### StoryBlocks — B2B API, subscription model nebrání prohledávání

API na `api.storyblocks.com` s HMAC autentizací (public key + secret + timestamp). Pouze B2B, vyžaduje jednání s obchodním oddělením. Free trial: neomezené vyhledávání + 5 stažení. Parametr `contributor_portal_id` pro filtrování podle contributora.

Veřejné search na `storyblocks.com/images/search/{query}` funguje **bez přihlášení** — subscription model nebrání prohlížení. Web je **JavaScript SPA** — HTTP klient nestačí, nutný headless browser. Žádné veřejné contributor stránky na consumer site.

### Envato — fragmentovaný ekosystém po akvizici

**Envato akvizitován Shutterstockem v květnu 2024 za $245M.** PhotoDune je v maintenance/sunset mode od masivního purge portfolií v 2016. Envato Elements (`elements.envato.com`) je nyní primární platforma pro stock fotky.

Envato Market API na `build.envato.com` s Personal Token/OAuth 2.0 pokrývá **pouze Envato Market** (PhotoDune, ThemeForest, CodeCanyon), **nikoli Envato Elements**. Pro Elements neexistuje veřejné API. Cloudflare + reCAPTCHA chrání web. „Looks Like" visual search je dostupný i pro nepřihlášené.

### PIXTA — bez API, japonský trh

Největší japonská fotobanka se **114,8M+ assety**. Žádné veřejné API nebylo nalezeno. Search funguje bez přihlášení na `pixtastock.com` (mezinárodní) i `pixta.jp` (japonský). Contributor portfolia vyžadují znalost URL. Image ID jsou numerické. Standard server-rendered web, nižší anti-bot ochrana. **Jazykové/locale zvážení nutné** — primární jazyk je japonština.

### MostPhotos — minimální informace, vysoká bariéra

Malá švédská fotobanka. **Žádné API**, web vrací **405 (Method Not Allowed)** na programatické požadavky. Téměř žádná technická dokumentace. Vyžaduje plnou browser automatizaci (Playwright/Selenium) s reverse engineeringem struktury webu.

### 500px — zrušené API, licensing přes Getty

Public API zrušeno v červnu 2018 po akvizici Visual China Group. Licencování nyní probíhá přes **distribuční partnery Getty Images a VCG**. Wab je JavaScript-heavy SPA. Interní GraphQL/REST API volání jsou pozorovatelná přes DevTools, ale neoficiální a nestabilní. Profily na `500px.com/{username}` a foto stránky na `500px.com/photo/{id}/{slug}` jsou veřejné.

### CanStockPhoto — ukončen

**Definitivně ukončil provoz 1. října 2023** po téměř 20 letech. Web zobrazuje pouze oznámení o uzavření. Důvody: klesající obchod, rostoucí náklady, smartphony, AI generování obrázků. Jednoduchý HTTP GET na `canstockphoto.com` potvrdí neoperativní stav.

---

## Návrh implementační architektury

### Pipeline overview

```
INPUT (CSV řádek + lokální soubor)
    │
    ▼
[1. METADATA EXTRACTION]
    ├── Čtení CSV: filename, description, title, contributor
    ├── EXIF extraction z lokálního souboru (datum, rozlišení, GPS)
    ├── Perceptuální hash lokálního souboru (pHash, dHash, wHash)
    └── CLIP embedding lokálního souboru (předpočítané)
    │
    ▼
[2. QUERY GENERATION] (per-bank adapter)
    ├── Textový dotaz z description/title/keywords
    ├── Contributor name/ID mapping
    ├── Pokud znám asset ID → přímý lookup
    └── Reverse image search URL/upload (kde API podporuje)
    │
    ▼
[3. CANDIDATE DISCOVERY] (paralelně per-bank)
    ├── API search (Shutterstock, Adobe, 123RF, DepositPhotos, Freepik)
    ├── Portfolio page scrape (Shutterstock /g/USER, DepositPhotos)
    ├── CDN URL probe (Alamy, Pond5 — prediktovatelné URL)
    ├── Web search + headless browser (Dreamstime, StoryBlocks, 500px)
    └── Reverse image search API (TinEye, Google Vision jako fallback)
    │
    ▼
[4. CANDIDATE METADATA NORMALIZATION]
    ├── Jednotný formát: {bank, asset_id, title, description, contributor,
    │     dimensions, thumbnail_url, detail_url, raw_response}
    └── Deduplikace kandidátů
    │
    ▼
[5. THUMBNAIL DOWNLOAD & PREPROCESSING]
    ├── Stažení preview/thumbnail z CDN URL
    ├── Resize na společnou velikost (256×256)
    ├── Výpočet perceptuálních hashů kandidáta
    └── CLIP embedding kandidáta
    │
    ▼
[6. IMAGE SIMILARITY SCORING]
    ├── Stage 1: pHash Hamming distance (práh ≤10 pro 64-bit)
    ├── Stage 2: SSIM + SIFT feature matching (pro kandidáty z Stage 1)
    ├── Stage 3: CLIP cosine similarity (tiebreaker, práh ≥0.90)
    └── Agregovaný similarity score
    │
    ▼
[7. CONFIDENCE SCORING & DECISION]
    ├── Kombinace: image_similarity + text_overlap + contributor_match
    │     + dimensions_match + url_pattern_match
    ├── Prahy: ≥0.80 → AUTO_PRESENT, ≤0.30 → AUTO_ABSENT, jinak UNCERTAIN
    └── Penalizace za ambiguous near-duplicates
    │
    ▼
[8. OUTPUT & AUDIT]
    ├── CSV/JSON výstup: {photo_id, bank, status, confidence, evidence_url,
    │     thumbnail_path, similarity_scores, timestamp}
    ├── Screenshot evidence (Playwright)
    ├── Manual review queue pro UNCERTAIN
    └── Audit log s kompletní historií
```

### Bank-specific adapter pattern

Každá fotobanka implementuje rozhraní `BankAdapter`:

```python
class BankAdapter(ABC):
    @abstractmethod
    def search_by_text(self, query: str, contributor: str = None) -> list[Candidate]
    @abstractmethod
    def search_by_image(self, image_path: str) -> list[Candidate]
    @abstractmethod  
    def check_asset_exists(self, asset_id: str) -> bool | None
    @abstractmethod
    def get_preview_url(self, candidate: Candidate) -> str | None
    @abstractmethod
    def get_rate_limiter(self) -> RateLimiter
```

Adaptery se dělí do tří kategorií podle primárního přístupu: **API-first** (Shutterstock, Adobe, 123RF, DepositPhotos, Freepik, BigStock), **CDN-probe** (Alamy, Pond5), **headless-browser** (Dreamstime, StoryBlocks, Envato, PIXTA, Vecteezy, 500px).

---

## Návrh scoring modelu

### Vstupní signály a jejich váhy

Confidence score se počítá jako vážená kombinace několika nezávislých signálů. Každý signál je normalizován na rozsah 0.0–1.0:

**Image similarity** (váha 0.35) — nejsilnější signál. Kombinuje pHash distance, SIFT feature match ratio a CLIP cosine similarity. Pro watermarked thumbnaily je CLIP nejrobustnější (watermark minimálně ovlivňuje sémantický embedding), zatímco pHash přidává ~3–8 bitů distance kvůli watermarku. SSIM je příliš citlivé na watermark pro samostatné použití, ale funguje jako doplňkový signál.

**Text overlap** (váha 0.25) — porovnání title/description z CSV s metadaty kandidáta. Jaccard similarity na úrovni slov, s normalizací (lowercase, odstranění stop words, stemming). Description match je silnější než title match, protože title se na bankách často liší od originálního názvu souboru.

**Contributor match** (váha 0.20) — binární nebo fuzzy match contributor identity z CSV proti jménu/pseudonymu na bance. Přesná shoda = 1.0, fuzzy match (Levenshtein distance ≤ 2) = 0.7, žádná shoda = 0.0. Pokud contributor match je 1.0, výrazně zvyšuje celkovou důvěru.

**Dimensions match** (váha 0.10) — porovnání aspect ratio lokálního souboru s reportovanými rozměry na bance. Přesná shoda aspect ratio (s tolerancí ±0.02) = 1.0, blízká shoda = 0.5, odlišná = 0.0. Banky občas cropují nebo mění rozlišení, proto nízká váha.

**URL/structural signals** (váha 0.10) — shoda filename v URL slug, přítomnost asset ID v databázi, konzistentní timestamp (datum uploadu vs. EXIF capture date).

### Penalizace

Ambiguous near-duplicates: pokud existuje více kandidátů s image_similarity > 0.70 ale < 0.90, aplikuje se **penalizace -0.15** na confidence, protože jde pravděpodobně o sérii podobných fotek od stejného contributora. Model penalizuje i situaci, kdy contributor match je negativní ale image similarity je vysoká (možný reupload jiným uživatelem — vyžaduje manuální review).

### Rozhodovací prahy

| Confidence | Rozhodnutí | Akce |
|-----------|-----------|------|
| **≥ 0.80** | `AUTO_PRESENT` | Automaticky označit jako živé, zaznamenat evidence |
| **0.50–0.79** | `UNCERTAIN_LIKELY` | Pravděpodobně přítomné, zařadit do review queue s prioritou |
| **0.30–0.49** | `UNCERTAIN_UNLIKELY` | Pravděpodobně nepřítomné, ale ověřit manuálně |
| **≤ 0.29** | `AUTO_ABSENT` | Automaticky označit jako nenalezené |

### Rozhodovací strom per banka

Příklad pro **Shutterstock** (API-first):

```
1. Je znám asset ID?
   ├── ANO → API GET /v2/images/{id}
   │   ├── HTTP 200 → PRESENT (confidence 0.95)
   │   └── HTTP 404 → ABSENT (confidence 0.90)
   └── NE → pokračuj
2. Je znám contributor username?
   ├── ANO → Scrape portfolio /g/USERNAME (všechny stránky)
   │   ├── Pro každý kandidát: stáhnout 260nw thumbnail, porovnat pHash
   │   ├── pHash distance ≤ 5 → PRESENT (confidence 0.85+)
   │   ├── pHash distance 6-12 → UNCERTAIN → Stage 2 (CLIP)
   │   └── Žádný kandidát pod 12 → pokračuj na text search
   └── NE → pokračuj
3. Text search přes API (description keywords + contributor filter)
   ├── Kandidáti nalezeni → thumbnail comparison pipeline
   └── Žádní kandidáti → pokus o reverse image search přes CV endpoint
4. CV reverse image search
   ├── Shoda nalezena → PRESENT (confidence závisí na similarity score)
   └── Žádná shoda → ABSENT (confidence 0.70 — search nemusí být vyčerpávající)
```

---

## Konkrétní doporučení pro implementaci v Pythonu

### Technologický stack

**HTTP klient**: `curl_cffi` pro veškeré HTTP požadavky mimo API. Tato knihovna impersonuje **TLS fingerprint prohlížeče** (Chrome, Safari, Edge), čímž obchází základní JA3/JA4 detekci, která blokuje standardní Python `requests`. Pro API volání je vhodný `httpx[http2]` s HTTP/2 podporou.

```python
from curl_cffi import requests as cf_requests
# Impersonuje Chrome TLS fingerprint
response = cf_requests.get(
    "https://www.shutterstock.com/g/contributor_name",
    impersonate="chrome",
    headers={"Accept-Language": "en-US,en;q=0.5"}
)
```

**Headless browser**: `playwright` s `playwright-stealth` pro JS-rendered stránky (StoryBlocks, 500px, Envato Elements). Playwright poskytuje nativní Python API, multi-browser podporu a built-in auto-wait. Stealth plugin patchuje `navigator.webdriver` a další detekční signály.

**Image processing**: `imagehash` (pHash, dHash, wHash), `Pillow` (pre-processing), `opencv-python` (SIFT feature matching, SSIM přes `skimage.metrics`), `open-clip-torch` nebo `transformers` (CLIP embeddings). Pro batch zpracování tisíců obrázků je kritické **předpočítat hashe** lokálních souborů a uložit do SQLite/CSV.

**Retry logika**: `tenacity` s exponential backoff + jitter. Konfigurace per-bank, protože rate limity se dramaticky liší (Shutterstock free: 100/hod, Adobe: nedokumentované, 123RF: nedokumentované).

```python
from tenacity import retry, wait_exponential_jitter, stop_after_attempt

@retry(wait=wait_exponential_jitter(initial=2, max=60, jitter=3), stop=stop_after_attempt(5))
def fetch_with_retry(url, session):
    response = session.get(url)
    if response.status_code in (429, 503):
        raise Exception(f"Rate limited: {response.status_code}")
    return response
```

### Doporučený víceúrovňový image matching pipeline

Fáze 1 zpracovává **tisíce obrázků za sekundu**: `imagehash.phash()` s `hash_size=16` (256-bitový hash pro lepší diskriminaci ve velkých katalozích). Hamming distance ≤ 25 pro 256-bit hash propouští kandidáty do další fáze. Pro 64-bitový hash (default `hash_size=8`) je práh ≤ 10.

Fáze 2 vyžaduje **10–200ms na pár**: SIFT feature matching s Lowe's ratio testem (threshold 0.75) a geometrická verifikace přes `cv2.findHomography()` s RANSAC. Pokud ≥ 4 inliery tvoří konzistentní geometrickou transformaci, jde o stejný obrázek s vysokou pravděpodobností. SSIM jako doplňkový signál (ale pozor na degradaci kvůli watermarkům — očekávané skóre 0.3–0.6 pro watermarked thumbnaily).

Fáze 3 jako tiebreaker: **CLIP ViT-L/14** cosine similarity. Na GPU ~5–20ms na obrázek, na CPU ~100–500ms. Práh ≥ 0.92 = garantovaný duplikát, 0.85–0.92 = velmi pravděpodobná shoda. CLIP je **nejrobustnější metoda vůči watermarkům** — sémantický embedding je minimálně ovlivněn.

### Reverse image search API jako universální fallback

**TinEye API** je nejefektivnější fallback pro celoplošné ověření. Index 70+ miliard obrázků, cenově od $0.01/search (milion searchů za $10K/rok) do $0.04/search (5000 za $200/rok). Python klient `pytineye`. TinEye exceluje v nalezení resized, cropped a watermarked verzí — ideální pro tento use case.

**Google Cloud Vision Web Detection** za $3.50/1000 požadavků identifikuje, kde se obrázek na webu zobrazuje, včetně stock foto stránek. Prvních 1000 měsíčně zdarma. Méně přesný než TinEye pro stock-specifické vyhledávání, ale širší pokrytí.

### Práce s anti-bot ochranou — praktická realita

Většina fotobank vrací **HTTP 403** na běžné Python požadavky. `curl_cffi` s `impersonate="chrome"` obchází základní TLS fingerprinting, ale nestačí proti Cloudflare Bot Management nebo Akamai Bot Manager s JS challenges. Pro tyto případy je nutný Playwright.

**Konkrétní ochranné systémy** (ověřené a odvozené): Adobe Stock používá **Akamai** (cookie `_abck`), Getty/iStock **Amazon CloudFront WAF**, Freepik pravděpodobně **Cloudflare**, Envato **Cloudflare + reCAPTCHA**. Shutterstock nemá identifikovaný specifický anti-bot systém, ale search stránky vyžadují JS rendering. Pond5 vrací silné 403 (pravděpodobně Cloudflare). Vecteezy potvrzeno 403 na web i API docs.

**Důležité**: contributor portfolio stránky mají **výrazně slabší ochranu** než search stránky. Shutterstock `/g/USERNAME` byl úspěšně fetchován prostým HTTP klientem. Toto je obecný pattern — statické portfolio stránky jsou často server-rendered a méně chráněné.

### Caching a evidence

Všechny HTTP odpovědi cachovat v lokálním SQLite s TTL 24 hodin (konfigurovatelné per-bank). Ukládat: URL, HTTP status, response headers, body hash, timestamp. Pro audit evidence: Playwright screenshoty detail stránek, HTML snapshoty, metadata JSON dumpy. Evidence directory struktura: `evidence/{bank}/{photo_id}/{timestamp}/`.

### Kdy CDN thumbnail URL probe stačí a kdy ne

Přímý HTTP HEAD request na thumbnail CDN URL je **nejrychlejší metoda** (< 100ms), ale s **důležitými caveaty**: Adobe Stock explicitně varuje, že CDN thumbnaily **přežívají stažení assetu** — obrázek může být z webu odstraněn, ale thumbnail na ftcdn.net stále existuje. Shutterstock thumbnaily na picdn.net mohou mít podobný problém. Naopak, Alamy CDN (`c7.alamy.com/comp/{ID}`) a Pond5 CDN (`ec.pond5.com/s3/`) jsou **spolehlivějšími indikátory** existence, protože tyto menší banky nemají tak agresivní CDN caching.

**Doporučení**: CDN probe používat jako **rychlý pre-filter** (HTTP 404 = pravděpodobně neexistuje), ale nikdy jako jediný zdroj pravdy pro pozitivní výsledek. Vždy potvrzovat přes API nebo search.

### Spolehlivost negativního výsledku

Rozhodnutí „fotka tam není" je inherentně méně spolehlivé než „fotka tam je", kvůli několika faktorům. Search výsledky jsou **omezené** — většina API vrací max 100–500 výsledků na stránku s limitem celkového offsetu (123RF: 10000 stránek, ale reálně relevantní výsledky jsou v prvních desítkách). Textové vyhledávání nemusí najít fotku s odlišným titulkem/popisem. Nově schválené fotky mohou mít **cache delay** 1–48 hodin. Hidden-but-live assety existují u bank, které zobrazují jen podmnožinu portfolia ve výsledcích.

**Mitigace**: kombinovat text search (description fragmenty) + contributor portfolio scrape (pokud je znám contributor) + reverse image search. Pokud všechny tři metody shodně vracejí „nenalezeno", confidence pro ABSENT je 0.85+. Pokud jen text search vrací prázdno, confidence pro ABSENT je pouze 0.50–0.65.

---

## Závěr

Automatická verifikace veřejné dostupnosti fotografií na fotobankách je **technicky proveditelná, ale vyžaduje bank-specific přístup**. Neexistuje jediná univerzální metoda. Pět bank tvoří **Tier 1** pro spolehlivou automatizaci: Shutterstock (API + portfolio), Adobe Stock (Files API — pokud získáte klíč), DepositPhotos (API s polem status), 123RF (bezplatné API), a Freepik (self-serve API s $5 kreditem). Tyto banky pokrývají majoritní podíl trhu a nabízejí strukturovaná API s přímou odpovědí na otázku „je asset živý?".

Getty Images zůstává problematická kvůli nepřístupnému self-service API — ověření vyžaduje buď obchodní vztah, nebo headless browser s rizikem nestability. Menší banky (PIXTA, MostPhotos, 500px) nemají API a spoléhají na scraping, který je provozně křehký. CanStockPhoto je mrtvý.

Nejsilnější implementační pattern je **tříúrovňový matching**: rychlý perceptuální hash jako filtr (pHash, ~5ms/pár), SIFT feature matching jako potvrzení (~200ms/pár), a CLIP jako sémantický tiebreaker (~20ms/pár na GPU). Tento pipeline správně identifikuje shodu i přes watermarky, resizing a JPEG kompresi typické pro stock preview obrázky.

Nečekaným zjištěním je, že **contributor portfolio stránky jsou obecně lépe přístupné** než search stránky — mají slabší anti-bot ochranu a často server-side rendering. Pro fotografa kontrolujícího vlastní portfolio je optimální strategií nejprve procházet vlastní contributor page (kde zná username), stahovat thumbnaily a porovnávat perceptuálním hashem, a teprve poté eskalovat na API search nebo reverse image search pro assety, které na portfoliu chybí ale mohou být „hidden-but-live".

Celkový odhad implementačního úsilí: **funkční prototyp pro Tier 1 banky (5 bank) v Pythonu je realizovatelný za 2–3 týdny** jedním vývojářem, s dalšími 2–3 týdny na Tier 2 banky a robustní error handling. Produkční nasazení s audit logováním, manuální review queue a monitoring vyžaduje další měsíc práce.