# Claude Analysis: Rework Direction for `markphotomediaapprovalstatusauto`

## Základ zadání

Systém má jeden jasný produkt:

- Pokud je aktivum s jistotou zákaznicky viditelné → zapsat `FOUND` (označit jako schváleno).
- Ve všech ostatních případech → `NOT FOUND` (neurčitý výsledek, odesílat do manuálního módu).
- `NOT FOUND` nesmí nikdy znamenat `zamítnuto` a nesmí přepisovat existující stav.

Toto je záměrně konzervativní volba. Falešná negativní (aktivum je live, ale systém ho nenajde) = zbytečná práce pro manuální mód. Falešná pozitivní (aktivum není live, ale systém ho označí jako `FOUND`) = nekritická data corruption. Asymetrie volby: **optimalizovat pro nula false positives, ne pro maximální míru automatizace.**

---

## Proč je potřeba přepis, ne oprava

Současný kód na větvi `feature/public-portfolio-approval` postavil celou detekci na shodu titulků z portfolio stránek. To je základně špatná architektura ze tří důvodů, které se kombinují:

**1. Titulky nejsou spolehlivý identifikátor.**
Fotobanky tituly po nahrání SEO-optimalizují, lokalizují do desítek jazyků a zkracují. Titulek v PhotoMedia.csv je stav *při nahrání*, titulek na zákaznickém webu je stav *dnes po úpravách banky*. Tyto dvě hodnoty nemusí být totožné.

**2. Scraped text z portfolií není customer-side view.**
Portfolio scraping (`/g/USERNAME`, `/artist/NAME`) ukazuje co přispěvatel nahrál — ne nutně co je zákaznicky dohledatelné přes search. Fotobanky asynchronně indexují: schválení v contributor portálu → asynchronní generování náhledů → distribuce do CDN → zápis do zákaznického indexu. Tyto fáze trvají minuty až dny. Portfolio stránka může zobrazovat aktivum, které ještě není v zákaznickém indexu.

**3. Title-only matching produkuje false positives při shhodě jiné fotky stejného titulu.**
V portfoliu jednoho autora jsou série snímků s podobnými nebo totožnými tituly. Title match neumí rozlišit mezi nimi.

**Závěr:** celá vrstva `public_portfolio/` (adapter pattern, runner, portfolio crawling jako primární zdroj důkazů) musí být přestavěna. Co lze zachovat:
- CLI rozhraní (`--banks`, `--dry-run`, `--report-dir`)
- CSV loading/writing logika
- logging infrastruktura
- test struktura

---

## Správná architektura: dvě fáze

### Fáze 1 — Candidate Discovery

Cíl: najít na dané fotobanky jednoho nebo více kandidátů, kteří by mohli být hledaným aktivem.

Metody (v pořadí spolehlivosti):
1. **API search** — strukturovaný dotaz s identitou contributora, klíčovými slovy, ID aktiva
2. **CDN check** — pokud je URL pattern CDN prediktovatelný z ID, HTTP HEAD request potvrdí existenci náhledu
3. **Web search** — fulltext search na zákaznickém webu s contributor filtrem
4. **Portfolio scraping** — záložní zdroj kandidátů, nikdy ne zdroj důkazů

### Fáze 2 — Candidate Verification

Cíl: ověřit, že nalezený kandidát je skutečně hledané aktivum, ne jiná fotka.

Primární metoda: **perceptuální hašování (pHash / dHash)** mezi lokální kopií aktiva a staženým náhledem.

Bez vizuálního ověření nelze vydat `FOUND`. Titulek ani klíčová slova nejsou dostatečné. Identita contributora je nutná podmínka, ale ne postačující — autor mohl na dané fotobanky nahrát více vizuálně podobných fotek s totožným titulkem.

---

## Scoring model

Ze čtveřice MD Research zdrojů (zejm. "Analýza dostupnosti fotografií na fotobankách") vychází tento váhový model jako nejkonkrétnější a nejodůvodněnější:

| Signál | Váha | Výpočet |
|---|---|---|
| dHash vzdálenost | 50 % | `1 - (HammingDistance / HashSize)` |
| Identita contributora | 20 % | Binární (1.0 = shoda jména/ID) |
| Klíčová slova | 15 % | Jaccardův index |
| Barevný hash | 10 % | `1 - (ColorDistance / Threshold)` |
| Titulek | 5 % | Levenshteinova vzdálenost |

**Threshold pro `FOUND`:** ≥ 0.92 agregovaného skóre.

Ale: vzhledem k požadavku nulových false positives a existenci manuálního módu jako záchytné sítě doporučuji přísnější konfiguraci:

- pHash Hammingova vzdálenost **≤ 2** (ne ≤ 8 jak uvádějí obecné zdroje) — watermarky a JPEG rekompresi tolerujeme, ale AI upscaling fotobank může vzdálenost zvýšit
- contributor identity **povinná** (ne volitelná) jako nutná podmínka bez ohledu na score
- `FOUND` pouze pokud jsou splněny **obě**: pHash ≤ 2 + contributor match

Systém může generovat skóre a logovat ho do audit reportu, ale rozhodovací logika je binární: dvě podmínky splněny → `FOUND`, jinak → `NOT FOUND`.

---

## Specifika per banka: co výzkum říká konkrétně

Codex-analysis se správně zabývá API dostupností. Tato sekce přidává konkrétní technické detaily z MD Research, které jsou přímo actionable.

### Shutterstock

**Kritické omezení, které Codex-analysis nezmiňuje explicitně:**
Free-tier API prohledává pouze **omezenou podmnožinu knihovny** (Free photos), nikoli celý katalog. Fotka přítomná na shutterstock.com se v API free-tieru nemusí vůbec objevit. Pro verifikaci přítomnosti celého portfolia je free API nefunkční.

**Praktický důsledek:** Portfolio scraping (`/g/USERNAME`) je pro naši use case *lepší než free-tier API*, protože zobrazuje skutečný obsah portfolia.

**CDN pattern (bez watermarku):**
`image.shutterstock.com/image-photo/{SLUG}-260nw-{ID}.jpg` — thumbnaily 260px bez Shutterstock watermarku, přímo konstruovatelné z ID. Vhodné pro pHash bez preprocessing.

**Rate limit free API:** 100 volání/hodinu, CV endpointy 5/minutu.

**Stack:** Portfolio scraping pro candidate discovery + 260nw thumbnail download + pHash.

---

### Adobe Stock

**Silný API, ale nově omezený přístup:**
API na `stock.adobe.io` bylo nejsilnějším nástrojem, ale od 2024 je omezeno na Stock for Enterprise zákazníky a Adobe Affiliates. Pro neregistrované vývojáře vyžaduje schválení přes Adobe Prerelease program. Stávající klíče fungují, ale ne každý je má.

**Pokud API není dostupné:**
Contributor stránky `stock.adobe.com/contributor/{creator_id}/{name}` jsou veřejně přístupné jako Akamai CDN + React SPA. Vyžadují JS rendering (Playwright).

**CDN pattern:**
`as{1-4}.ftcdn.net/v2/jpg/{AA}/{BB}/{CC}/{DD}/{SIZE}_F_{ASSET_ID}_{HASH}.jpg` — hash nelze odvodit z ID, nutno získat z API nebo ze stránky aktiva. Malé thumbnaily (110–240px) jsou bez watermarku.

**Specifická schopnost:** Adobe Stock umožňuje search-by-image přes `search_parameters[similar_url]` nebo `search_parameters[similar_image]` (upload). To je nejbezpečnější verifikační metoda — vizuální podobnost na straně Adobe.

**Stack:** API-first (pokud klíč existuje) + similar-image search pro verifikaci; Playwright fallback pro contributor page.

---

### Getty Images / iStock

**API:** Jednotné API v3 (`api.gettyimages.com`), ale **není self-service** — vyžaduje kontakt s obchodním oddělením. `GET /v3/images/{id}` vrací HTTP 200 = aktivum live, 404 = neexistuje.

**Enhanced search (2024):** Getty nasadilo ML-based "enhanced search" interpretující přirozený jazyk. Vypnout lze přes `enhanced_search=false` pro přesné výsledky.

**Preview URL:** obsahují neprediktovatelný hash (`media.gettyimages.com?s={size}&h={hash}`), nelze konstruovat z ID — nutno získat z odpovědi API nebo z renderované stránky.

**Stack:** Playwright-first s `enhanced_search=false` v query params; API pokud je dohodnutý přístup.

---

### DepositPhotos

**Klíčové zjištění z výzkumu:** DepositPhotos stránky obsahují `__NEXT_DATA__` JSON blok (Next.js aplikace) přístupný bez JavaScript renderování. Extrakce přímo z HTML dává ID a statusy bez nutnosti Playwright.

**API:** Příkaz `dp_command=getMediaData` vrací pole `status: "active"` — přímé potvrzení že aktivum je live. API klíč přes `depositphotos.com/api-program/signup.html` (program/partner přístup).

**Contributor portfolio:** `depositphotos.com/portfolio-{userid}.html`, PHP backend s Backbone.js, částečně server-rendered → nepotřebuje tak agresivní JS rendering jako AdobeStock/Getty.

**Stack:** `__NEXT_DATA__` extrakce z HTML jako primární cesta; Playwright fallback; API pokud je dostupné.

---

### 123RF

**Nejdostupnější API pro naši use case:**
Bezplatné non-commercial klíče přes `123rf.com/api/key/apply.php` (schválení ~24 hodin). `getInfo` endpoint vrací: popis, klíčová slova, jméno contributora, dimensions, kategorii. `search` endpoint: až 100 výsledků, paginace do 10 000 stránek.

**Anti-bot ochrana:** Mírná, žádný Cloudflare Bot Management ani DataDome. Web je převážně server-rendered.

**CDN pattern:** `us-cdn{1-4}.123rf.com/168nwm/{contributor}/{folder}/{filename}/{id}-{slug}.jpg` — watermarked, ale vhodné pro pHash s tolerancí watermarku.

**Stack:** API-first (`httpx`); CDN direct download pro pHash.

---

### Pond5

**Nejjednodušší CDN check ze všech bank:**
Pond5 používá prediktovatelný CDN pattern na `ec.pond5.com/s3/`:
- ID padded na 9 číslic
- `{padded_id}_icon.jpeg` (120×66px)
- `{padded_id}_iconm.jpeg` (240×134px)
- `{padded_id}_iconl.jpeg` (480×268px)
- `{padded_id}_prevstill.jpeg` (1280×720px)

HTTP HEAD request na konstruovanou URL bez autentizace: HTTP 200 = aktivum existuje v CDN. Pak stáhnout `_iconm` pro pHash.

**Upozornění:** Pond5 byl akvizitován Shutterstockem v 2022, status API je nejistý (dokumentace naposledy aktualizována 2018). CDN check je proto spolehlivější než API pro long-term stabilitu.

**Web search:** Vrací 403 na přímé HTTP požadavky (Cloudflare). Playwright nutný jako fallback.

**Stack:** CDN HEAD check + pHash jako primární cesta; API pokud je funkční; Playwright jako záložní.

---

### Dreamstime

**Bez session cookies nepoužitelné:** Jak je dokumentováno v BLOCKED_BANKS. Dreamstime vrací 403 nebo CAPTCHA bez přihlášení.

**S contributor účtem:** Public advanced search na `dreamstime.com/photos-images/{keyword}.html` podporuje filtr `Only from Contributor(s)`. Contributor profily `dreamstime.com/{username}_info` jsou veřejné.

**API:** Vyžaduje registraci a manuální schválení. WordPress plugin odhalil `$apiUrl = 'http://www.dreamstime.com/api/'`, session-based autentizace.

**Stack:** Playwright se session cookies z přihlášeného přispěvatele; contributor-filtered search; API pokud bude schváleno.

---

### AdobeStock (bez přístupu k API)

**URL slug extraction jako fallback:**
`stock.adobe.com/images/{slug}/{id}` — slug v URL je verzí titulku. Použitelné pro candidate discovery, ale ne pro verifikaci identity.

**Stack bez API:** Playwright na contributor stránce + pHash z ftcdn.net náhledů.

---

### Alamy

**Důležitá změna:** Contributor portfolio bylo zrušeno v 02/2025 (dle compass report). Portfolio scraping na Alamy již nefunguje jako candidate discovery.

**API:** OAuth 2.0, partnerský vztah. Dokumentace na Stoplight (SPA, vyžaduje JS).

**Fallback:** CDN preview check. `c7.alamy.com/comp/{id}/{title}-{id}.jpg` — watermarked comp preview, přístupný volně. Lze konstruovat z ID.

**Stack:** CDN comp preview pro candidate existence; Playwright pro zákaznický search; API pokud partnerský přístup.

---

### Freepik

**Self-serve API:** `api.freepik.com/v1/resources` s API klíčem (bez obchodního jednání). Vrací `url`, `author.name`, `thumbnail.url`. Nejčistší API pro naši use case po 123RF.

**Stack:** `httpx` API-first; preview similarity z `thumbnail.url`.

---

### Vecteezy

**Placené API** ($40/měsíc pro plný přístup). CDN na webu vrací 403 na přímé requesty.

**Stack:** API pokud je subscription; jinak low priority.

---

### Ostatní banky (nízká priorita)

| Banka | Situace |
|---|---|
| Bigstock | Shutterstock subsidiary; contributor-scoped search na webu; API deprecated |
| Storyblocks | B2B API; bez klíčů Playwright na SPA (bez portfolia) |
| Envato | Market API existuje, Elements nemá; Playwright pro Elements search |
| PIXTA | Web search + image search UI; author number v HTML; Playwright nutný |
| MostPhotos | Playwright; item pages mají stable ID a contributor jméno |
| 500px | API zrušeno 2018; Playwright pouze; nízká priorita |
| CanStockPhoto | Uzavřeno 10/2023; neimplementovat |

---

## Kde se tato analýza liší od Codex-analysis

Codex-analysis je strategicky správný. Přidám konkrétní technické detaily, které Codex neobsahuje:

**1. Shutterstock free-tier API omezení je fatální pro naši use case.**
Codex doporučuje API-first pro Shutterstock. Ale free-tier API neprohledává celý katalog. Portfolio scraping + CDN thumbnail je pro naši use case (verifikace vlastního portfolia) lepší cesta než nefunkční API.

**2. Pond5 CDN check je nejrychlejší first win.**
Codex nezmiňuje CDN pattern. Pond5 má 1 403 schválených fotek v CSV a prediktovatelný CDN URL. CDN HEAD check + pHash je implementovatelné bez API klíčů v řádu dní.

**3. DepositPhotos `__NEXT_DATA__` eliminuje Playwright pro candidate discovery.**
Next.js stránky obsahují JSON s metadaty přímo v HTML. Playwright je potřeba jen jako fallback, ne jako default.

**4. pHash threshold pro FOUND: ≤ 2, ne ≤ 8.**
Codex pHash zmiňuje obecně. Při požadavku nulových false positives je threshold ≤ 8 příliš tolerantní (povoluje AI-generované obrázky podobné originálu). Threshold ≤ 2 toleruje watermark a JPEG kompresi ale odmítne vizuálně podobné, ale odlišné snímky.

**5. Alamy portfolio je od 02/2025 zrušeno.**
Tato informace je z compass reportu. Codex-analysis s tím nepočítá.

**6. Single-contributor context mění false positive riziko.**
Výzkumné zdroje obecně varují před title matching v kontextu celého katalogu milionů fotek. My prohledáváme vždy jen vlastní portfolio jednoho přispěvatele. False positive riziko je nižší, ale stále existuje (série podobných fotek od stejného autora). Proto pHash zůstává nutný, ale threshold může být mírně tolerantnější než pro whole-catalog search.

---

## Co zachovat z existujícího kódu

| Komponenta | Zachovat? | Poznámka |
|---|---|---|
| CLI interface (`--banks`, `--dry-run`) | ✅ | Dobré rozhraní |
| CSV loading/writing | ✅ | Funguje správně |
| Logging infrastruktura | ✅ | Shared logger OK |
| `browser.py` / Playwright setup | ✅ s úpravami | Locale fix již v commitu; zachovat jako fallback vrstvu |
| `matching.py` (title matching) | ⚠️ částečně | Zachovat jako slabý signál (5 % váha) v scoring modelu; nikdy jako standalone důkaz |
| `banks/` adaptery (výpočet title z URL) | ❌ překonat | Candidate discovery přes URL slug je použitelné, ale nestačí bez pHash |
| `runner.py` jako monolith | ❌ rozdělit | Refaktorizovat na: `discover_candidates()`, `verify_candidate()`, `build_evidence()`, `write_result()` |
| `validate_detection.py` | 🗑️ temporary | Smazat po přechodu na novou architekturu |

---

## Doporučená implementační sekvence

### Sprint 1 — pHash základ (bez sítě)
1. Implementovat `pHash` / `dHash` generátor pro lokální soubory z PhotoMedia.csv
2. Cache hashe do SQLite nebo JSON souboru (lokálně, gitignored)
3. Implementovat `compare_previews(local_path, remote_url) → HammingDistance`
4. Unit testy s fixtures (stejná fotka, různé komprese, vodoznaky, jiná fotka)

### Sprint 2 — Pond5 první
1. CDN HEAD check pro existenci (`ec.pond5.com/s3/{padded_id}_iconm.jpeg`)
2. Stáhnout thumbnail, spustit pHash comparison
3. Contributor jméno z URL nebo z metadata jako povinná podmínka
4. Výstup: `FOUND` / `NOT FOUND` + audit log

### Sprint 3 — 123RF (API)
1. Registrovat API klíč
2. `httpx` search endpoint s contributor name
3. Stáhnout `link_image`, pHash comparison + contributor match
4. Dimenze jako třetí signál

### Sprint 4 — Shutterstock (portfolio + CDN)
1. Portfolio scraping jako candidate discovery (zachovat z existujícího kódu)
2. Konstruovat 260nw CDN URL z ID v portfoliu
3. pHash comparison

### Sprint 5 — DepositPhotos (`__NEXT_DATA__`)
1. Contributor search na webu
2. Parsovat `__NEXT_DATA__` JSON z HTML (bez Playwright)
3. pHash z static CDN thumbnailů

### Sprint 6 — ostatní banky
- AdobeStock (API pokud dostupné, jinak Playwright + ftcdn.net pHash)
- GettyImages (Playwright, `enhanced_search=false`)
- Dreamstime (Playwright se session cookies)
- Freepik (httpx API-first)

---

## Audit report (povinný výstup)

Každý výsledek musí obsahovat:

| Pole | Popis |
|---|---|
| `local_file` | Cesta k lokálnímu souboru |
| `bank` | Název fotobanky |
| `result` | `FOUND` / `NOT FOUND` |
| `candidate_url` | URL kde byl kandidát nalezen |
| `candidate_id` | ID aktiva na fotobanky pokud dostupné |
| `contributor_match` | `True` / `False` |
| `phash_distance` | Hammingova vzdálenost (0–64) |
| `dhash_distance` | Hammingova vzdálenost (0–64) |
| `dimension_match` | `True` / `False` / `Unknown` |
| `preview_url` | URL staženého náhledu |
| `reason` | Textový kód důvodu rozhodnutí |
| `timestamp` | ISO 8601 |

Report se generuje vždy — při `--dry-run` i při reálném běhu.

---

## Zdroje

Tato analýza vychází z těchto MD Research souborů:

- `MD Research/Analýza dostupnosti fotografií na fotobankách.txt` — scoring model, weighted verification pipeline, bank-by-bank API detaily
- `MD Research/compass_artifact_wf-...md` — CDN URL patterns, Shutterstock free-tier omezení, Alamy portfolio zrušení, bank tier classification
- `MD Research/zprava-hluboky-vyzkum.md` — PRESENT/ABSENT/UNCERTAIN architektura, candidate discovery + verification
- `MD Research/Analýzy COpilot.txt` — pHash/CLIP threshold doporučení, audit log požadavky
- `MD Research/Analýza Perplexity.txt` — contributor identity + image similarity jako kombinace
- `codex-analysis.md` — Codex samostatná analýza (FOUND/NOT FOUND model, bank tier tabulka)
