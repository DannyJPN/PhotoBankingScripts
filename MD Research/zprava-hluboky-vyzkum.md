# Robustní detekce, zda je konkrétní fotografie veřejně „live“ na fotobankách

## Executive summary

Tento průzkum se soustředí výhradně na customer‑side realitu: **zda je konkrétní fotografie veřejně dohledatelná / zobrazitelná na zákaznickém webu dané fotobanky** – nikoli na interní stavy typu *approved/published* v contributor dashboardu.

Nejspolehlivější automatizovatelná odpověď na otázku „je fotka veřejně live?“ prakticky vždy vzniká jako **kombinace dvou kroků**:

1) **Candidate discovery (najít kandidáty)** – získat malou množinu pravděpodobných výsledků z veřejného katalogu (ideálně přes oficiální API nebo stabilní zákaznické vyhledávání / portfolio).  
2) **Důkaz shody (verifikace)** – stáhnout zákaznický **preview/thumbnail** a potvrdit shodu s lokálním souborem pomocí **perceptual similarity** (pHash/SSIM/CLIP embedding) + doplňkových metadatových signálů (autor, aspect ratio, popis).  

Klíčový závěr: **„PRESENT“ (ANO) lze často rozhodnout robustně**, pokud existuje cesta k preview obrázkům a aspoň jedno stabilní vyhledávání/portfolio. Naproti tomu **„ABSENT“ (NE) je běžně nespolehlivé**, protože většina veřejných vyhledávání je neexhaustivní (ranking, limit výsledků, personalizace, regionalizace, lazy‑load), a proto je bezpečnější výstup **„UNCERTAIN“**, pokud nemáte „coverage důkaz“, že jste prohledali katalog dostatečně kompletně.

### Kde je automatizace realisticky nejlepší

Tier 1 (nejlepší pro automatické workflow) v praxi znamená: **máte oficiální (nebo quasi‑public) search API a z něj preview URL**, případně velmi stabilní veřejné endpointy, plus možnost filtrovat podle autora/podobnosti.

- **Adobe Stock** – oficiální API umí vyhledávání i „similar to image/asset“ a vrací thumbnail URL; navíc existuje veřejné „Find similar“ UI. citeturn16search16turn6view4  
- **123RF** – oficiální API je přímočaré (vyhledávání vrací ID + thumbnail URL) a web má „search by image“. citeturn25view0turn13view1  
- **Pond5** – dokumentované API má search bez loginu a dokumentuje konstrukci preview obrázků z `icon_base` + ID. citeturn22view0turn24view0  
- **Freepik** – API je standardní API‑key autentizace (server‑to‑server) a zahrnuje „Stock content API“. citeturn26view1turn26view2  
- **Storyblocks** – existuje API s test klíči / partner přístupem; veřejné search UI také existuje. citeturn27search4turn27search6turn15search2  

Tier 2 (použitelné, ale s omezeními): typicky **žádné snadno dostupné API**, ale existuje robustní webové vyhledávání + filtr na autora, nebo veřejné portfolio a stabilní preview.

- **Dreamstime** – veřejné vyhledávání obsahuje filtr „Only from Contributor(s)“; API je partner‑type (vyžaduje přihlášení pro žádost o přístup). citeturn32view1turn32view0  
- **Alamy** – autor nejde hledat přímo v hlavním search boxu, ale lze filtrovat ve výsledcích „Search by contributor name“; a platforma explicitně pracuje s booleovskými dotazy. citeturn33view0turn31view1  
- **PIXTA** – veřejné item stránky mají „item number“ a autor ID; existuje „Search by Image“ UI. citeturn3search33turn4search2  
- **MostPhotos** – veřejné user stránky + item ID jsou dostupné. citeturn18search4turn18search3  

Tier 3 (jen doplněk / fallback): typicky silné JS/anti‑bot, nedostupné API, nebo vysoká nestabilita scraping signálů.

- **Depositphotos** – web vyžaduje JS a má „Reverse Image Search“, ale robustní automatizace bez oficiálních klíčů bývá provozně křehká; jejich Enterprise API je pro enterprise klienty (klíč „od managera“). citeturn13view0turn16search9  
- **Vecteezy** – veřejný web je chráněn reCAPTCHA; API existuje, ale mimo API je riziko bot‑frikce vysoké. citeturn28view0turn28view1turn14view3  
- **Envato** – existuje Envato Market API (vyžaduje Envato účet), ale nelze automaticky předpokládat, že pokrývá „Envato Elements“ katalog; bez jasného API pro Elements je to spíš web‑fallback. citeturn17search0turn17search6  
- **500px** – veřejné API bylo ukončeno (free access), takže automatizace je primárně web‑based a méně stabilní. citeturn20view1  

Tier 4 (neinvestovat): **Can Stock Photo ukončeno.** citeturn19search2  

Doporučený praktický rámec: stavět systém jako **bank‑independent matching framework** s bank‑specific „adaptery“, kde banky s API jedou „HTTP only“, a banky s JS/anti‑bot jedou „headless only“ + konzervativní „UNCERTAIN“ výstupy.

## Srovnávací tabulka fotobank

Poznámky k interpretaci sloupců:

- **Bez loginu?** = zda lze jako anonymní návštěvník získat aspoň search/preview/customer stránku.  
- **S contributor loginem?** = zda by contributor login mohl pomoci (např. zobrazit veřejný profil/portfolio link), ale bez reliance na interní statusy.  
- **API?** = existuje oficiální API; v praxi rozlišuji **self‑service / klíč** vs **partner‑only**.  
- **Preview dostupné?** = lze získat thumbnail/preview URL (API nebo web) pro image‑similarity potvrzení.  
- **Primární přístup** vždy míří na customer‑side realitu: nejdřív candidate discovery, potom image similarity.

| Banka | Bez loginu? | S contributor loginem užitečné? | API? | Veřejné search rozhraní? | Portfolio použitelné pro kandidáty? | Preview dostupné pro similarity? | Vhodný primární přístup | Riziko false positive | Riziko false negative | Doporučená priorita |
|---|---:|---:|---|---:|---:|---:|---|---|---|---|
| entity["company","Shutterstock","stock media platform"] | ano | ano | ano (API) | ano | ano (veřejný profil) | ano (přes API) | API search → preview similarity | střední | střední | Tier 1 (pokud API) |
| entity["company","Adobe Stock","stock media marketplace"] | ano | ano | ano (API key) | ano | ano (author page) | ano (API thumbnails) | API search/similar → preview similarity | nízké–střední | střední (index delay) | Tier 1 |
| entity["company","Getty Images","photo licensing company"] | ano | spíš okrajově | ano (partner) | ano | nejisté | ano (web previews) | partner API nebo web search → similarity | střední | střední–vyšší | Tier 2 |
| entity["company","iStock","stock photo brand"] | ano | spíš okrajově | nepřímo (Getty) | ano | nejisté | ano (web previews) | web search → similarity | střední | střední–vyšší | Tier 2 |
| entity["company","Depositphotos","stock media marketplace"] | ano (JS) | málo | ano (enterprise) | ano (JS) | ano (pravděpod.) | ano (web previews) | web + (reverse image search UI) → similarity | střední | vyšší | Tier 3 |
| entity["company","123RF","stock media marketplace"] | ano | ano | ano (api_key) | ano | ano (pravděpod.) | ano (API link_image) | API search → preview similarity | nízké–střední | střední | Tier 1 |
| entity["company","Pond5","stock media marketplace"] | ano | okrajově | ano (dokumentové) | ano | nejisté | ano (icon_base → preview) | API search → preview similarity | nízké–střední | střední | Tier 1–2 |
| entity["company","Dreamstime","stock photo marketplace"] | ano | okrajově | ano (partner) | ano | částečně | ano (web previews) | web search + contributor filter → similarity | nízké–střední | střední–vyšší | Tier 2 |
| entity["company","Bigstock","stock photo marketplace"] | ano | okrajově | ano (API program) | ano | nejisté | ano (web previews) | web search → similarity; API jen pokud máte | střední | střední–vyšší | Tier 2–3 |
| entity["company","Alamy","stock photo agency"] | ano | okrajově | ano (partner/JS) | ano | ano (přes filtr autora) | ano (web previews) | web boolean search → filter contributor → similarity | nízké–střední | střední | Tier 2 |
| entity["company","Freepik","design assets platform"] | ano | málo | ano (API key) | ano | spíš ne | ano (API / web) | API resource search → preview similarity | střední | střední | Tier 1–2 |
| entity["company","Vecteezy","stock assets platform"] | ano (reCAPTCHA) | málo | ano (API plány) | ano | nejisté | ano (API i web) | API (pokud máte) → preview similarity | střední | vyšší bez API | Tier 2–3 |
| entity["company","Storyblocks","stock media service"] | ano | málo | ano (partner/test keys) | ano | nejisté | ano (API/web) | API (test keys) nebo web → similarity | střední | střední | Tier 2 |
| entity["company","Envato","digital asset marketplace"] | ano | málo | ano (Market API) | ano | nejisté | ano (web) | Market API (kde relevantní) jinak web → similarity | střední | vyšší | Tier 3 |
| entity["company","PIXTA","stock media marketplace japan"] | ano | okrajově | nejasné | ano | ano (autor ID) | ano (sample/preview) | Search by Image + autor → similarity | nízké–střední | střední | Tier 2 |
| entity["company","Mostphotos","stock photo agency nordics"] | ano | okrajově | nejasné | ano (přes web) | ano (user page) | ano (web) | user page → preview similarity | nízké–střední | střední | Tier 2 |
| entity["company","500px","photo community licensing"] | ano | okrajově | ne (API shut down) | ano | ano (profil) | ano (web) | web → similarity (konzervativně) | střední | vyšší | Tier 3 |
| entity["company","Can Stock Photo","stock photo site closed"] | ne | ne | ne | ne | ne | ne | neinvestovat | — | — | Tier 4 |

## Detailní rozbor podle fotobank

Níže je pro každou fotobanku strukturovaný a implementačně zaměřený rozbor v sekcích A–H. Tam, kde nelze z veřejných zdrojů spolehlivě potvrdit konkrétní technický detail (např. interní JSON payloady), je to explicitně označeno jako **hypotéza** a nedoporučuje se na tom postavit primární produkční rozhodování.

### Shutterstock

**A. Přístupové možnosti**  
Shutterstock má oficiální API pro vyhledávání, metadata a preview (integrační model typicky vyžaduje API přístup/klíč). citeturn16search27 Z contributor dokumentace plyne existence veřejného portfolia na zákaznickém webu a tvrzení, že akceptovaný obsah je na customer webu publikován a dohledatelný. citeturn10search4turn10search2 Prakticky: mimo API může být scraping/prohlížení veřejných stránek provozně křehké (rate‑limit, bot ochrany; zde nelze z dostupných zdrojů exaktně potvrdit technologii ochrany).

**B. Nejlepší „source of truth“ pro „je live?“ (seřazení)**  
1) **Oficiální Shutterstock API (search + preview)** – nejlepší pro automatizaci, protože vrací strukturovaná data a preview. citeturn16search27  
2) **Veřejné portfolio autora na Shutterstock.com** – dobré pro candidate discovery, ale samo o sobě není důkaz identity fotky bez image similarity. citeturn10search2turn10search4  
3) **Veřejné search UI** – použitelné, ale více rizik: limit výsledků, personalizace, změny frontendu.

**C. Metoda identifikace konkrétní fotografie**  
Customer‑side nejspolehlivější: **preview/thumbnail similarity** (pHash/SSIM/CLIP) + **contributor identity** + **aspect ratio**. Title matching je slabý (uživatelský požadavek správně).  
- **Strong match**: preview similarity vysoká (viz scoring model níže) *a zároveň* sedí autor/portfolio.  
- **Weak match**: sedí popis/klíčová slova, ale image similarity jen střední (riziko near‑duplicates).  
- **Riskantní**: pouze textová shoda bez similarity.

**D. Praktická implementace**  
- Candidate discovery: generovat 2–5 dotazů z popisu (rare bigram/trigram) + případný filtr na autora (pokud API umožní) → top N kandidátů → stáhnout preview.  
- Verifikace: pHash + (volitelně) CLIP embedding similarity; rozhodnout.  
- Naprosté minimum: ukládat důkazní artefakty (URL kandidáta, preview bytes, hash, score).

**E. Odolnost a provozní rizika**  
Bez API typicky vyšší riziko anti‑bot a nestability selectů. Doporučení: v produkci preferovat API; při blokaci webu vracet UNCERTAIN, nikoli se snažit blokace obcházet.

**F. Konzervativní decision tree**  
- **ANO**: nalezen kandidát přes API/portfolio a image similarity překročila „auto present“ práh *a* autor sedí.  
- **NEJISTÉ**: nalezen kandidát s hraniční similarity, nebo nelze stáhnout preview, nebo je candidate set příliš široký.  
- **NE**: pouze pokud máte „coverage důkaz“ (např. kompletní enumerace portfolia přes API/portfolio) a žádný kandidát neprošel.

**G. Prioritizace**: Tier 1 (při API), jinak Tier 2–3.

**H. Konkrétní implementační návrh**  
- Primární: API search → preview download → similarity proof. citeturn16search27  
- Sekundární: veřejné portfolio → enumerace → preview similarity. citeturn10search4turn10search2  
- Fallback: externí reverse image (např. TinEye API) pro dohledání výskytu na webu; použitelný jako doplněk. citeturn4search24  
- Vstupy: lokální soubor + description + (ideálně) contributor handle.  
- Typ matchingu: pHash/SSIM/CLIP + autor + aspect ratio.  
- Spolehlivost: vysoká pro „ANO“; nízká pro „NE“ bez coverage.  
- Hlavní rizika: near‑duplicate série, anti‑bot webu, omezené search výsledky.  
- Produkce: API‑first, robustní caching, audit trail.

### Adobe Stock

**A. Přístupové možnosti**  
Adobe Stock lze prohledávat bez loginu a UI přímo nabízí „Find similar“ (upload/drag‑and‑drop image). citeturn6view4 Oficiální Adobe Stock API podporuje vyhledání podle keywordů i podle contributora, a vrací URL pro thumbnails. citeturn16search16 Existují veřejné contributor/author stránky (URL vzor `/contributor/<id>/<name>`). citeturn9search19

**B. Nejlepší „source of truth“**  
1) **Adobe Stock API search / similar** – strukturované výsledky, thumbnail URL, možnost filtrovat; nejlepší. citeturn16search16  
2) **Veřejný author/contributor listing** – dobrý candidate source, zejména pokud znáte contributor ID. citeturn9search19  
3) **Veřejné search UI + Visual Search (Find similar)** – použitelné i bez API. citeturn6view4  
4) **Item detail stránky** – potvrzení, že asset je veřejný; vhodné pro audit.

**C. Identifikace konkrétní fotky**  
Adobe API výslovně říká, že výsledky obsahují thumbnail URL. citeturn16search16 To je ideální pro pHash/SSIM.  
- Strong match: vysoká image similarity + shoda contributora nebo autor stránky.  
- Pozor na indexaci: v komunitních odpovědích se objevuje realita, že asset může být schválený, ale dočasně nevyhledatelný (indexing issue / delay). citeturn9search13

**D. Praktická implementace**  
- Candidate discovery (API):  
  - Vygenerovat dotazy z popisu (vzácná fráze).  
  - Pokud máte contributor identity, použít contributor filtr (API to podporuje). citeturn16search16  
  - Stáhnout thumbnails → similarity.  
- Candidate discovery (bez API): Playwright otevře search, použije „Find similar“ upload (cust‑side). citeturn6view4  
- Audit: ukládat screenshot výsledků / URL výsledku / stažený thumbnail.

**E. Rizika**  
- Zpoždění indexace: typicky hodiny až dny; existují případy „not properly indexed“. citeturn9search13  
- Lokalizace (region/language) – UI se přesměrovává podle regionu. citeturn5view1

**F. Decision tree**  
- **ANO**: API najde kandidáta a similarity překročí práh; nebo Visual Search vrátí identický asset a detail stránka je dostupná.  
- **NEJISTÉ**: žádný match, ale upload byl „příliš široký“ / limit výsledků / možné index delay. citeturn9search13  
- **NE**: až po opakovaném ověření s odstupem (např. 48–72 h) + portfolio enumerace.

**G. Prioritizace**: Tier 1.

**H. Konkrétní implementační návrh**  
- Primární: Adobe Stock API (search + thumbnails) → similarity scoring. citeturn16search16  
- Sekundární: contributor page → získat kandidáty → thumbnail similarity. citeturn9search19  
- Fallback: Visual Search (Find similar) přes headless upload. citeturn6view4  
- Vstupy: lokální soubor, description; ideálně contributor ID.  
- Matching: pHash + CLIP embedding; text jen pomocně.  
- Spolehlivost: vysoká (ANO), střední (NE) kvůli indexaci. citeturn9search13  
- Produkce: plánovat „recheck window“ po uploadu.

### Getty Images / iStock

**A. Přístupové možnosti**  
Veřejné vyhledávání bez loginu existuje (Getty i iStock veřejně zobrazují výsledky). citeturn5view2turn5view3 Getty má oficiální API (typicky integrační/partner přístup). citeturn0search2  
Prakticky: bez partner API je potřeba opatrný web‑based workflow, protože pro „NE“ je riziko false negative vyšší (omezené výsledky, personalizace).

**B. Nejlepší „source of truth“**  
1) **Getty API (pokud máte)** – nejlépe strukturované vyhledání. citeturn0search2  
2) **Veřejné search UI + item detail** – customer‑side důkaz, že image existuje a je veřejně přístupná. citeturn5view2turn5view3  
3) **Autor/portfolio stránky** – nejisté (ne všude konzistentní, často bez snadných filtrů); bez tvrdého zdroje nedoporučuji spoléhat jako primární.

**C. Identifikace**  
Bez API je klíčové: preview similarity + doplňkové signály (rozlišení/aspect). Slabé: title.  
Zvláštní riziko: mnoho stock katalogů má near‑duplicate editorial série; nutná penalizace podobných clusterů.

**D. Praktická implementace**  
- Candidate discovery: generovat unikátní dotazy (rare phrase) a použít web search.  
- Kandidáty agregovat do top N (např. 50), stáhnout thumbnails (pokud URL snadno extractovat).  
- Pokud web stránka neposkytuje stabilní thumbnail URL bez JS, použít Playwright (request interception) a ukládat JSON/response jako audit (hypotéza; konkrétní payloady nelze z veřejných zdrojů spolehlivě garantovat).

**E. Rizika**  
- Search není exhaustivní; závěr „není tam“ bez coverage je slabý.  
- Lokalizace regionem a A/B testy mohou měnit HTML.

**F. Decision tree**  
- **ANO**: nalezen detail asset a preview similarity je vysoká.  
- **NEJISTÉ**: nic nenalezeno, nebo nelze stáhnout preview, nebo výsledky omezené.  
- **NE**: jen pokud máte partner API + opakované testy s různými dotazy + (ideálně) autor filtr.

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: partner API (pokud dostupné) nebo web search → preview similarity. citeturn0search2turn5view2turn5view3  
- Sekundární: reverse image search externě (např. TinEye) pro dohledání výskytu „na webu“. citeturn4search24  
- Fallback: ruční queue pro sporné případy.

### Depositphotos

**A. Přístupové možnosti**  
Depositphotos webové vyhledávání existuje, ale stránka může vyžadovat JavaScript; v navigaci je uvedeno „Reverse Image Search“ a „API Suite“. citeturn13view0 Enterprise API je explicitně pro corporate klienty a vyžaduje enterprise účet a klíč poskytnutý manažerem. citeturn16search9

**B. Nejlepší „source of truth“**  
1) **Reverse image search UI (pokud funguje bez loginu / s minimální registrací)** – může být nejlepší candidate discovery bez title. citeturn13view0  
2) **Veřejné search UI** – jako candidate source; potvrzení přes preview similarity. citeturn13view0  
3) **Enterprise API** – pouze pokud máte enterprise přístup; pak je to Tier 1 pro vás. citeturn16search9

**C. Identifikace**  
Preferované: preview similarity.  
Text: description je užitečný pro generování dotazu, ale ne pro důkaz.  
Strong match: vysoká similarity + shoda autora (pokud je dostupná v UI/metadata).

**D. Praktická implementace**  
- Candidate discovery:  
  - 1) headless (Playwright) otevře Reverse Image Search a nahraje lokální image; získá top N výsledků.  
  - 2) fallback: text search podle rare phrase.  
- Candidate scoring: stáhnout thumbnails a podobnost.

**E. Rizika**  
- JS‑heavy + možné anti‑bot; při změně UI vysoká údržba. citeturn13view0  
- False negatives: limity výsledků a ranking.

**F. Decision tree**  
- **ANO**: Reverse image search vrátí identický asset a similarity je vysoká.  
- **NEJISTÉ**: Reverse image search vrací podobné, ale ne identické; nebo upload selže.  
- **NE**: jen pokud reverse image search (opakovaně) nic relevantního nenajde + máte coverage (např. autor portfolio).

**G. Prioritizace**: Tier 3 (bez enterprise klíčů), Tier 1–2 (s enterprise).

**H. Konkrétní implementační návrh**  
- Primární: Reverse Image Search UI → preview similarity. citeturn13view0  
- Sekundární: text search + filtrování + similarity.  
- Fallback: enterprise API, pokud dostupné. citeturn16search9  

### 123RF

**A. Přístupové možnosti**  
123RF má jasně dokumentované API, kde vyhledávání probíhá přes `method=search&api_key=...` a výsledky obsahují `id`, `link_image` (thumbnail) a `description` (a volitelně `width/height`). citeturn25view0 Veřejné UI obsahuje „Search by image“ s možností drag‑and‑drop. citeturn13view1

**B. Nejlepší „source of truth“**  
1) **Oficiální 123RF API search → thumbnail similarity** – nejlepší kombinace. citeturn25view0  
2) **Search by image UI** – silný fallback pro candidate discovery bez title. citeturn13view1  
3) **Item detail** – audit/konfirmace.

**C. Identifikace**  
Silné identifikátory customer‑side: thumbnail URL (`link_image`) + media `id` + rozměry (pokud nastavíte `app=1`). citeturn25view0  
Strong match:  
- pHash vzdálenost nízká + CLIP similarity vysoká,  
- rozměry/aspect sedí v toleranci,  
- (volitelně) shoda popisu.

**D. Praktická implementace**  
- Query generation: z description vytěžit 2–3 unikátní fráze; poslat 2–3 API dotazy (různé kombinace) a sjednotit kandidáty.  
- Candidate scoring: stáhnout `link_image` a porovnat.  
- Log: ukládat JSON z API + stažený thumbnail + metriky.

**E. Rizika**  
- False positives hlavně u near‑duplicates; řešit penalizací clusterů (viz scoring).  
- Rate limiting: respektovat.

**F. Decision tree**  
- **ANO**: nalezen API kandidát s vysokou image similarity.  
- **NEJISTÉ**: žádný kandidát, ale description/metadata slabé (málo unikátní).  
- **NE**: jen pokud máte coverage (autor portfolio / více dotazů + image search UI).

**G. Prioritizace**: Tier 1.

**H. Konkrétní implementační návrh**  
- Primární: API → thumbnail similarity. citeturn25view0  
- Sekundární: search by image UI headless upload. citeturn13view1  
- Fallback: externí reverse image (TinEye) pro dohledání výskytu. citeturn4search24  

### Pond5

**A. Přístupové možnosti**  
Pond5 má veřejně dostupnou API referenci. V ní je `search` endpoint explicitně označen „Login required: no“. citeturn22view0 Dále dokumentuje konstrukci ikon/preview: z `icon_base` a ID vytvoříte např. `000590216_icon.jpeg` a dokonce `000590216_prevstill.jpeg`. citeturn24view0

**B. Nejlepší „source of truth“**  
1) **Pond5 API search + preview still/thumbnail similarity** – ideální kombinace. citeturn22view0turn24view0  
2) **API get_clip_data (metadata o klipu) + preview** – potvrzení detailů. citeturn24view0  
3) **Web search UI** – fallback.

**C. Identifikace**  
Customer‑side extrémně silné: standardizovaná konstrukce preview z ID + `icon_base`. citeturn24view0  
To umožňuje robustní pHash/SSIM nad normalizovaným preview still.

**D. Praktická implementace**  
- Candidate discovery: API `search` s dotazem ze description; případně sort by username (v API je parametr `sb` zahrnující `username`). citeturn22view0  
- Candidate retrieval: stáhnout `prevstill` nebo `iconl` a porovnat. citeturn24view0  
- Rate limiting: konzervativně (25–100 výsledků/page), caching.

**E. Rizika**  
- Dokumentace je z roku 2018; možné změny endpointů/URL vzorů (nutné validační testy). citeturn21view0turn29view1  
- Watermark/preview transformace mohou měnit pHash; proto kombinovat metriky.

**F. Decision tree**  
- **ANO**: API vrátí kandidáta, stáhnete preview still a similarity je vysoká.  
- **NEJISTÉ**: preview je nedostupné, nebo API vrací jen volné shody.  
- **NE**: jen s coverage (typicky autor/portfolio enumerace + opakované dotazy).

**G. Prioritizace**: Tier 1–2 (v praxi podle toho, zda je API stabilně použitelná ve vašem prostředí).

**H. Konkrétní implementační návrh**  
- Primární: API search → preview still download → similarity. citeturn22view0turn24view0  
- Sekundární: get_clip_data pro detailní metadata a audit. citeturn24view0  
- Fallback: web UI headless.

### Dreamstime

**A. Přístupové možnosti**  
Dreamstime má veřejné search bez loginu a ve filtrech uvádí „Only from Contributor(s)“ – zásadní pro zúžení kandidátů na vaše portfolio. citeturn32view1 Oficiální API existuje, ale „Login to request access“ naznačuje partner/affiliate přístup, nikoli čistě self‑service. citeturn32view0

**B. Nejlepší „source of truth“**  
1) **Veřejné search UI + contributor filter → preview similarity** – prakticky nejrobustnější bez API. citeturn32view1  
2) **Dreamstime API (pokud máte přístup)** – zlepší stabilitu automatizace. citeturn32view0  
3) **Item detail** – audit.

**C. Identifikace**  
- Strong match: thumbnail similarity + autor filtr ve výsledcích. citeturn32view1  
- Weak match: jen textové shody (u Dreamstime to bude často mnoho).

**D. Praktická implementace**  
- Candidate discovery: dotaz z rare phrase + aplikovat contributor filtr (přes UI). citeturn32view1  
- Candidate scoring: stáhnout thumbnails a porovnat.  
- Provoz: protože UI je bohaté a paginované, vyplatí se limitovat na top K stránek a výsledky cacheovat.

**E. Rizika**  
- Search limit/pagination → false negatives.  
- Rozdíly mezi „Latest uploads“ vs „Most relevant“ mohou ovlivnit dohledatelnost; doporučit zkusit více sortů.

**F. Decision tree**  
- **ANO**: contributor‑filtered kandidát + vysoká image similarity.  
- **NEJISTÉ**: nic nenalezeno, ale coverage nízká (např. autor má tisíce fotek).  
- **NE**: jen s coverage (např. pokud by šla enumerace portfolia bez limitu; bez důkazu raději UNCERTAIN).

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: web search + „Only from Contributor(s)“ → preview similarity. citeturn32view1  
- Sekundární: API (pokud získáte přístup). citeturn32view0  
- Fallback: externí reverse image.

### Bigstock

**A. Přístupové možnosti**  
Bigstock má veřejné item stránky, které uvádí „Stock Photo ID“. citeturn15search14 Dokumentace o veřejně dostupném API není spolehlivě potvrzená jako self‑service; z podmínek užití plyne existence „Bigstock’s API program“ (tedy API spíš jako program/partnerství). citeturn16search13

**B. Nejlepší „source of truth“**  
1) **Item detail stránka (s ID) + preview similarity** – pokud dokážete spolehlivě najít kandidáta. citeturn15search14  
2) **API program** – pokud máte přístup. citeturn16search13  
3) **Web search UI** – candidate source.

**C. Identifikace**  
- Silné: Stock Photo ID (pokud ho získáte), preview similarity. citeturn15search14  
- Slabé: title.

**D. Praktická implementace**  
- Candidate discovery: text search z rare phrase; u výsledků stáhnout preview; u kandidátů uložit Stock Photo ID do vlastní databáze (např. pro budoucí přímé dotazy). citeturn15search14  
- Pokud máte interně mapping na Bigstock ID (např. historicky), pak přímé item page check je „tvrdý“ důkaz.

**E. Rizika**  
- Bez API vyšší riziko false negatives (search výsledky omezené).  
- Možné změny v URL/structure.

**F. Decision tree**  
- **ANO**: nalezen item s ID a similarity vysoká. citeturn15search14  
- **NEJISTÉ**: nic nenalezeno; coverage nízká.  
- **NE**: vysoce konzervativně – spíš neautomatizovat.

**G. Prioritizace**: Tier 2–3.

**H. Konkrétní implementační návrh**  
- Primární: web search → preview similarity → uložit Stock Photo ID. citeturn15search14  
- Sekundární: API program (pokud dostupný). citeturn16search13  
- Fallback: externí reverse image.

### Alamy

**A. Přístupové možnosti**  
Alamy má booleovské vyhledávání a explicitně doporučuje používat uvozovky, boolean operátory a závorky pro přesnější dotazy. citeturn31view1 Zásadní: jméno fotografa/pseudonym **nejde hledat v hlavním search boxu**, ale ve výsledcích lze použít filtr „Search by contributor name“. citeturn33view0 Také uvádí, že po přidání caption/tagů jsou online po aktualizaci search enginu (typicky do 24h), což je customer‑side realistický „index delay“ signál. citeturn33view0

**B. Nejlepší „source of truth“**  
1) **Search UI (boolean + přesné fráze) → filtr contributor name → preview similarity** – nejpraktičtější. citeturn31view1turn33view0  
2) **Item detail stránky** – audit.  
3) **API** – existuje, ale veřejné detailní zpracování docs je JS‑gated; bez jistoty přístupu nedoporučuji jako klíčovou osu.

**C. Identifikace**  
- Strong match: přesná preview similarity + shoda contributor filtru. citeturn33view0  
- Pozor: autor nelze hledat přímo dotazem, takže candidate discovery musí být dvoufázové (nejdřív dotaz na obsah, potom filtr autora). citeturn33view0

**D. Praktická implementace**  
- Query generation: vytěžit z description 2–3 přesné fráze a dávat do uvozovek; doplnit boolean NOT pro časté rušivé termíny. citeturn31view1  
- Candidate retrieval: ze search výsledků aplikovat contributor filter; pak stáhnout prvních N preview a porovnat. citeturn33view0  
- Recheck: při „absent“ dělat recheck po 24–48h, protože Alamy popisuje aktualizaci indexu. citeturn33view0

**E. Rizika**  
- False negatives bez coverage: search výsledky mohou být obrovské.  
- Index delay.

**F. Decision tree**  
- **ANO**: (dotaz → contributor filter) poskytne kandidáta s vysokou similarity.  
- **NEJISTÉ**: nic nenalezeno, coverage nízká nebo čerstvé změny. citeturn33view0  
- **NE**: jen při opakovaném negativním výsledku + po recheck intervalu.

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: boolean search → contributor filter → preview similarity. citeturn31view1turn33view0  
- Sekundární: externí reverse image pro dohledání re‑uploadů. citeturn4search24  
- Fallback: ruční review u sporných clusterů.

### Freepik

**A. Přístupové možnosti**  
Freepik má moderní API dokumentaci. Autentizace je přes API key v hlavičce `x-freepik-api-key` a explicitně uvádí, že jde o **private API keys** a tedy **server‑to‑server calls**. citeturn26view2 Dokumentace zároveň zmiňuje „Stock content API“. citeturn26view1

**B. Nejlepší „source of truth“**  
1) **Freepik API (stock content) → preview similarity** – nejstabilnější. citeturn26view1turn26view2  
2) **Veřejný web search** – fallback.

**C. Identifikace**  
Silné: API resource ID + preview URL (konkrétní field názvy závisí na endpointu; nutné ověřit implementačně přes OpenAPI). citeturn26view2

**D. Praktická implementace**  
- Candidate discovery: z description udělat dotaz → API search endpoint (v rámci „Stock content API“). citeturn26view1  
- Similarity: použít pHash + CLIP (u ilustrací se pHash může chovat hůře; CLIP často pomůže).

**E. Rizika**  
- Bez API: scraping může být nestabilní.  
- U grafických assets (vektory/PSD) je preview ne vždy původní render.

**F. Decision tree**  
- **ANO**: API vrátí kandidáta s vysokou preview similarity.  
- **NEJISTÉ**: jen textové shody nebo preview chybí.  
- **NE**: jen s coverage (např. enumerace přes API „vše od autora“, pokud endpoint existuje).

**G. Prioritizace**: Tier 1–2.

**H. Konkrétní implementační návrh**  
- Primární: API‑key search → preview similarity. citeturn26view2turn26view1  
- Sekundární: web search + similarity.

### Vecteezy

**A. Přístupové možnosti**  
Vecteezy veřejný web uvádí ochranu reCAPTCHA (vyšší riziko bot‑frikce) a zároveň má veřejné stránky se „Search by Image“ v navigaci. citeturn28view0turn14view3 Současně existuje Vecteezy API s plány; stránky přímo uvádí, že API umí keyword search, filtry a mimo jiné nabízí „Un-watermarked Preview images“ (v rámci plánů). citeturn28view1

**B. Nejlepší „source of truth“**  
1) **Vecteezy API (pokud máte) → unwatermarked preview similarity** – nejlepší. citeturn28view1  
2) **Veřejný web search + Search by Image** – fallback, ale s reCAPTCHA rizikem. citeturn14view3turn28view0

**C. Identifikace**  
- Strong: API preview similarity + resource metadata. citeturn28view1  
- Na webu: stáhnout thumbnail z výsledků a porovnat; pozor na watermark.

**D. Praktická implementace**  
- Pokud API: používat čistě HTTP klient.  
- Bez API: Playwright; minimalizovat requesty; ukládat důkazy; při výskytu reCAPTCHA konzervativně UNCERTAIN (neobcházet).

**E. Rizika**  
- reCAPTCHA a anti‑bot → provozně nestabilní scraping. citeturn28view0  
- A/B HTML variace.

**F. Decision tree**  
- **ANO**: API/web najde kandidáta a similarity překročí práh.  
- **NEJISTÉ**: reCAPTCHA nebo limit výsledků.  
- **NE**: jen s coverage přes API.

**G. Prioritizace**: Tier 2–3 (podle dostupnosti API).

**H. Konkrétní implementační návrh**  
- Primární: Vecteezy API → preview similarity; audit JSON. citeturn28view1  
- Sekundární: web search + Search by Image (headless). citeturn14view3turn28view0  
- Fallback: externí reverse image.

### Storyblocks

**A. Přístupové možnosti**  
Veřejné search stránky pro „images“ existují. citeturn15search2 Storyblocks nabízí API s test účtem/klíči; business stránka uvádí možnost testování a „API test keys“. citeturn27search4 Postman requesty ukazují `/api/v2/images/search` a vyžadují `project_id` a `user_id`. citeturn27search6 Starší PDF dokumentace uvádí, že endpointy jsou dostupné „to our partners“ a uvádí domény a endpoint `/api/v1/stock-items/search`. citeturn29view1

**B. Nejlepší „source of truth“**  
1) **Storyblocks API (test keys/partner) → preview similarity** – nejstabilnější. citeturn27search4turn27search6turn29view1  
2) **Veřejné search UI** – fallback pro candidate discovery. citeturn15search2

**C. Identifikace**  
- Strong: API vrátí asset ID + preview; similarity rozhodne.  
- Bez API: web thumbnails + similarity; vyšší riziko DOM změn.

**D. Praktická implementace**  
- API režim: podpis/HMAC dle jejich API (detaily je potřeba číst v aktuální dokumentaci; z veřejných snippetů víme, že existuje autentizace a povinné identifikátory). citeturn27search6turn27search4  
- Web fallback: Playwright; z HTML získat kandidáty a stáhnout thumbnails.

**E. Rizika**  
- API historicky verze v PDF (2018) – je nutné validační testování, protože endpointy se mohly změnit. citeturn29view0turn29view1  
- Bez API: search stránky a filtry se mohou měnit.

**F. Decision tree**  
- **ANO**: kandidát + vysoká similarity.  
- **NEJISTÉ**: pouze textová shoda nebo omezené výsledky.  
- **NE**: jen pokud API dává možnost enumerace/coverage.

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: API (test keys) → search → preview similarity. citeturn27search4turn27search6  
- Sekundární: web search page → thumbnails → similarity. citeturn15search2

### Envato

**A. Přístupové možnosti**  
Envato má Envato Market API; dokumentace přímo říká, že lze postavit aplikaci napojenou na Envato Market a přistupovat i k funkcím typu search. citeturn17search0 API Terms uvádí, že pro plný přístup je potřeba Envato účet. citeturn17search6  
**Pozor (praktické omezení)**: z veřejných zdrojů nelze bezpečně tvrdit, že Envato Market API pokrývá i katalog Envato Elements (často odlišná služba). Proto se doporučuje rozlišit, kde přesně je vaše fotografie publikována.

**B. Nejlepší „source of truth“**  
1) **Market API (pokud relevantní pro váš katalog)** – strukturované. citeturn17search0turn17search6  
2) **Veřejné web item stránky/search (Elements)** – fallback.

**C. Identifikace**  
- Strong: preview similarity + item ID.  
- Weak: title.

**D. Praktická implementace**  
- Nejprve rozhodnout „Market vs Elements“.  
- Market: API token, search endpointy (viz build.envato.com). citeturn17search0  
- Elements: web scraping je spíše Playwright‑based; ale u „NE“ vysoké riziko false negative.

**E. Rizika**  
- Nejasné API pokrytí pro stock photos; riziko, že investujete do špatného adapteru.  
- Frontend změny.

**F. Decision tree**  
- **ANO**: existuje item page a preview match.  
- **NEJISTÉ**: nelze robustně prohledat nebo není jistý katalog.  
- **NE**: jen s coverage.

**G. Prioritizace**: Tier 3.

**H. Konkrétní implementační návrh**  
- Primární: Market API (kde relevantní). citeturn17search0turn17search6  
- Sekundární: web search + preview similarity (Playwright).  
- Fallback: UNCERTAIN + ruční queue.

### PIXTA

**A. Přístupové možnosti**  
PIXTA má veřejné search, včetně „Search by Image“ (drag & drop). citeturn4search2 Veřejné item stránky uvádějí „Item number“ a autora s ID, a říkají, že lze stáhnout watermarked sample data po free signup. citeturn3search33

**B. Nejlepší „source of truth“**  
1) **Search by Image UI** – nejlepší candidate discovery bez title. citeturn4search2  
2) **Item number + author ID + preview similarity** – potvrzení.

**C. Identifikace**  
- Strong: vysoká similarity vůči watermarked sample + shoda author ID. citeturn3search33  
- Pozor: watermark může ovlivnit pHash; kombinovat metriky.

**D. Praktická implementace**  
- Playwright: upload do Search by Image → získat kandidáty.  
- Stáhnout sample/preview a porovnat.

**E. Rizika**  
- Lokalizace a jazykové mutace, JS‑heavy.

**F. Decision tree**  
- **ANO**: item number nalezen + high similarity.  
- **NEJISTÉ**: upload vrací podobné, ale ne jasné.  
- **NE**: jen po opakovaném negativu.

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: Search by Image → preview similarity. citeturn4search2  
- Sekundární: text search + autor ID. citeturn3search33

### MostPhotos

**A. Přístupové možnosti**  
MostPhotos má veřejné user stránky (portfolio) a veřejné item stránky. citeturn18search4turn18search0 Item příklad uvádí ID ve tvaru `mp66894171`. citeturn18search3

**B. Nejlepší „source of truth“**  
1) **User page → enumerace kandidátů → preview similarity**. citeturn18search4  
2) **Item page s ID** – audit. citeturn18search3

**C. Identifikace**  
- Strong: preview similarity + (pokud známý) autor page.  
- Weak: text.

**D. Praktická implementace**  
- Candidate discovery: pokud znáte MostPhotos user handle, enumerovat poslední N (nové uploady) a porovnat.  
- Pokud handle neznáte: vyhledávání rare phrase + potom similarity.

**E. Rizika**  
- U velkých portfolií enumerace může být dlouhá → potřeba limit a caching.

**F. Decision tree**  
- **ANO**: nalezen kandidát v user portfoliu + high similarity.  
- **NEJISTÉ**: portfolio velké a neprohledané celé.  
- **NE**: jen pokud máte coverage.

**G. Prioritizace**: Tier 2.

**H. Konkrétní implementační návrh**  
- Primární: user page → candidate thumbnails → similarity. citeturn18search4  
- Sekundární: item page ID pro audit. citeturn18search3  

### 500px

**A. Přístupové možnosti**  
500px uvádí, že bezplatný přístup k API skončil a k 15.6.2018 byl API přístup vypnut. citeturn20view1 To znamená, že automatizace je primárně web‑based.

**B. Nejlepší „source of truth“**  
1) **Veřejné web stránky (profil/fotka) + preview similarity**.  
2) **RSS/feeds (pokud existují)** – jen doplňkově.

**C. Identifikace**  
Silná: preview similarity. Slabá: text/title.

**D. Praktická implementace**  
- Headless pro načtení stránky fotky a extrakci preview.  
- Vysoká opatrnost.

**E. Rizika**  
- Bez API: nestabilní HTML, možné rate‑limit.

**F. Decision tree**  
- **ANO**: existuje veřejná stránka fotky + similarity.  
- **NEJISTÉ**: pokud nelze získat preview.  
- **NE**: nedoporučuji automatizovat.

**G. Prioritizace**: Tier 3.

**H. Konkrétní implementační návrh**  
- Primární: web → similarity. citeturn20view1  
- Fallback: ruční.

### Can Stock Photo

**A–H shrnutí**: služba oznámila ukončení provozu. citeturn19search2 **Tier 4 – neinvestovat.**

## Implementační architektura

Cílem je produkční pipeline, která pro (lokální soubor + řádek v `PhotoMedia.csv`) vrátí:

- `present` (ANO) – konzervativně, s auditovatelným důkazem,
- `absent` (NE) – jen když je coverage dostatečná,
- `uncertain` (NEJISTÉ) – default pro slabé situace.

### Doporučený bank‑independent framework

**Vstupy (na úrovni jedné fotky)**  
- `file_path` (lokální JPG/PNG/…)
- `csv_row` (filename, description, keywords, optional title, optional contributor identity per banka)
- odvozené: `aspect_ratio`, `resolution`, `exif_timestamp` (když existuje)

**Krok 1: Normalizace a feature extract (lokálně)**  
- `sha256` souboru (jen interní deduplikace, ne match proti webu)  
- `pHash` (např. 64bit) z lokální fotky po standardizaci (resize, grayscale)  
- `CLIP embedding` (volitelně, ale velmi užitečné pro watermark/resize)  
- `color histogram` / jednoduché vizuální signály (fallback)  
- `text tokens` z description (stopwords pryč, lemmatizace, n‑gramy)

**Krok 2: Candidate discovery (bank adapter)**  
Každý adapter implementuje:

- `search_candidates(text_queries, contributor_hint, limit)`  
- `search_by_image(file_bytes)` (jen pokud banka má customer‑side „Find similar“ a je to v souladu s vašimi pravidly/ToS)  
- `enumerate_portfolio(contributor_id, since_date, limit)` (pokud existuje stabilní author page / API)

Výstup: seznam kandidátů s (minimálně) `candidate_id`, `candidate_url`, `preview_url`, `available_metadata`.

**Krok 3: Candidate scoring**  
Pro každý kandidát:

- stáhnout `preview_url` (uložit do evidence store)  
- spočítat `pHash` a/nebo `SSIM` vůči lokální fotce (po stejné normalizaci)  
- spočítat `CLIP cosine similarity` (pokud používáte)  
- textové skóre: overlap description/keywords (jen doplňkově)  
- autor skóre: shoda author ID / handle (pokud dostupné)

**Krok 4: Decision + evidence**  
- `present` pokud:  
  - existuje kandidát se silným image důkazem (pHash/SSIM/CLIP) a současně žádný „konfliktní signál“ (např. jiný autor, výrazně jiné AR).  
- `absent` pouze pokud:  
  - `coverage_score` je vysoké (např. úplná enumerace autor portfolia + image search UI + více text dotazů) a žádný kandidát neprošel.  
- jinak `uncertain`.

**Krok 5: Audit trail**  
U každého rozhodnutí ukládat:
- seznam dotazů (text/image), timestamp, bank, adapter verze,
- seznam kandidátů a jejich skóre,
- stažené preview obrázky (nebo jejich hash + cache key),
- URL kandidáta a případně snapshot HTML/JSON response.

### Anti‑bot a compliance poznámky (bez obcházení)

- Kde existuje oficiální API, **preferovat API** (nižší bot frikce, stabilnější). Např. Adobe Stock API, 123RF API, Pond5 API. citeturn16search16turn25view0turn22view0  
- U webů chráněných reCAPTCHA je automatizace mimo API riziková; při výskytu reCAPTCHA je produkčně rozumné vracet `uncertain` a poslat do ruční fronty. (Vecteezy zmiňuje reCAPTCHA přímo na stránce.) citeturn28view0  
- Neimplementovat „CAPTCHA solving“ nebo jiné obcházení ochran – jednak právně/ToS, jednak provozně (nestabilní).

## Scoring a rozhodovací model

Níže je praktický a konzervativní model. Váhy jsou průchozí pro první produkční iteraci; následně se kalibrují na vašich reálných datech (zlatý set: ručně potvrzené přítomnosti).

### Doporučené feature‑score komponenty

**Vizuální shoda (hlavní)**  
- `pHash_sim` (0–1): normalizace Hamming distance na [0,1]  
- `SSIM` (0–1): na downscalované šedotónové verzi  
- `CLIP_sim` (0–1): cosine similarity embeddingů

Doporučení: finální `image_confidence = max( w_phash*pHash_sim + w_ssim*SSIM + w_clip*CLIP_sim )` se saturací. Prakticky často stačí kombinace pHash + CLIP.

**Autor / portfolio shoda (silný podpůrný signál)**  
- `contributor_match`:  
  - +1 pokud candidate jasně patří danému contributorovi (ID/handle)  
  - 0 pokud neznámé  
  - −1 pokud prokazatelně jiný autor

**Metadatová shoda (slabší)**  
- `aspect_match`: +1 pokud AR v toleranci ±1–2 %  
- `desc_overlap`: Jaccard / token overlap (0–1)  
- `filename_match`: jen pokud banka vrací filename (ne všude)

### Konkrétní bodové váhy (příklad)

- `image_confidence * 65`  
- `contributor_match`:
  - +20 (shoda),
  - +0 (neznámé),
  - −30 (konflikt)  
- `aspect_match`:
  - +8 (shoda),
  - +0 (neznámé),
  - −8 (konflikt)  
- `desc_overlap * 7`  
- `near_duplicate_penalty`:
  - −10 až −25 pokud je v top N více kandidátů s podobným image score (typický znak série)

**Celkové skóre**: 0–100 (po ořezu do [0,100])

### Doporučené prahy

- **Auto PRESENT**: `score >= 85` a zároveň `image_confidence >= 0.92`  
- **Auto UNCERTAIN**: vše mezi (včetně situací, kdy nelze stáhnout preview)  
- **Auto ABSENT**: jen pokud `score < 20` *a současně* `coverage_score >= 0.85`

### Coverage score (aby „NE“ bylo obhajitelné)

Coverage je klíčová konstrukce, protože „není tam“ nelze vyvozovat z jednoho search dotazu.

Příklad komponent:

- +0.40 pokud jste udělali **portfolio enumeraci** (a máte důkaz, že je kompletní nebo alespoň pokrývá poslední X dní uploadů)  
- +0.30 pokud jste udělali **image‑based search** (Find similar / search by image) a výsledek je prázdný nebo bez relevantních kandidátů  
- +0.20 pokud jste udělali **více text dotazů** (min 3) a pro každý jste prošli min 3 stránky výsledků  
- +0.10 pokud jste dělali **recheck po čase** (např. 24–72h) – důležité na platformách s index delay (Adobe, Alamy). citeturn9search13turn33view0  

Bez coverage doporučení: **NE nikdy automaticky nevydávat**; vracet `uncertain`.

## Doporučení pro implementaci v Pythonu

### Kdy `requests/httpx` a kdy `Playwright`

**`httpx`/`requests` (preferovat)**  
Použít, když existuje API nebo jednoznačné veřejné endpointy a preview URL:
- Adobe Stock API (thumbnails v search výsledcích). citeturn16search16  
- 123RF API (vrací `link_image`). citeturn25view0  
- Pond5 (API + konstrukce preview still z `icon_base`). citeturn22view0turn24view0  
- Freepik API (server‑to‑server). citeturn26view2  

**`Playwright` (jen kde nutné)**  
Použít, když:
- stránka vyžaduje JS k vykreslení výsledků (Depositphotos explicitně hlásí „requires JavaScript“). citeturn13view0  
- chcete použít „Search by image“ UI bez API (Adobe/123RF/Vecteezy/PIXTA apod.). citeturn6view4turn13view1turn14view3turn4search2  
- potřebujete robustně stahovat preview z JS‑rendered DOM.

### Obrazové metody: pHash / SSIM / CLIP / OCR

- **pHash**: rychlá, dobrá pro resize/crop malé míry; citlivější na watermark.  
- **SSIM**: dobrý doplněk, ale pomalejší; citlivý na posuny/vodotisky.  
- **CLIP embedding**: bardzo užitečné pro watermark a drobné transformace; vyžaduje GPU/CPU výkon.  
- **OCR**: dávat až jako poslední fallback (např. když watermark obsahuje text a chcete ho odfiltrovat), ale obecně je OCR pro stock preview často kontraproduktivní.

Doporučený kompromis pro produkci:
- Tier 1 banky: pHash + CLIP (SSIM jen při hraničních případech).  
- Tier 2/3 web scraping: pHash + SSIM (CLIP jen pro false positive kontrolu).

### Cache, důkazy a testování

**Cache**  
- HTTP cache: ukládat odpovědi API/search (ETag/Last‑Modified kde existuje).  
- Preview cache: store preview images v adresáři podle `(bank, candidate_id, preview_hash)`.

**Audit důkazy**  
- Pro každý run ukládat JSONL: `input_id`, bank, queries, candidate list, scores, decision.  
- Preview bytes (nebo aspoň jejich hash + lokální cesta).  
- U Playwright navíc screenshot stránky s výsledky / detailu.

**Testování proti reálným vzorkům**  
- Vytvořit „golden set“: např. 200 fotek per banka, kde ručně ověříte `present/absent/uncertain` a uložíte jako ground truth.  
- Měřit: precision pro `present` (hlavní metrika), recall pro `present` (sekundární), a míru `uncertain` (má být přiměřená; u Tier 3 vyšší).

### Externí reverse image jako doplněk

Pokud potřebujete „web‑level“ důkaz (např. fotka se může objevit mimo vámi očekávaný search dotaz), má smysl použít **entity["company","TinEye","reverse image search"] API** jako doplněk; existuje přímo návod „Identifying stock photos with the TinEye API“. citeturn4search24  
To je užitečné zejména:
- když bankovní search UI je neexhaustivní,
- když existuje riziko re‑uploadu pod jiným title/keywords,
- když potřebujete důkaz, že se image už někde veřejně vyskytuje.

(Praktická poznámka: vyžaduje upload obrázku na službu třetí strany; to může být citlivé z hlediska interních pravidel/privátnosti.)

