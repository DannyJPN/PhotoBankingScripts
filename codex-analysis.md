# Codex Analysis: Rework Direction for `markphotomediaapprovalstatusauto`

## Goal and safety rule

The key product rule is asymmetric:

- A false negative is tolerable: the system may fail to prove that an asset is live even when it actually is.
- A false positive is not tolerable: the system must not say "present/live" unless the evidence is strong enough to make that conclusion operationally safe.

That rule changes the architecture materially. It means:

- the script output should be operationally binary: `FOUND` or `NOT FOUND`
- `FOUND` needs strong evidence
- `NOT FOUND` must not create `zamítnuto` and must not overwrite the existing status

This document expands the earlier verbal assessment into a source-backed technical position and validates API availability where it materially affects design.

## Executive position

### 1. What the research gets right

The research files are directionally correct on the most important point: title-based matching is not a safe foundation for this feature. Public/customer-side detection should be modeled as:

1. candidate discovery
2. candidate verification

That conclusion is supported by the currently documented capabilities of multiple banks:

- Adobe Stock officially documents search by metadata and also image-similarity search in the Stock Search API.[1][2]
- Shutterstock officially documents authenticated search plus reverse image search capability in its API offering.[3][4]
- 123RF officially documents search results that include stable media IDs and thumbnail URLs (`link_image`).[5]
- Freepik officially documents stock-content search and retrieval by ID via API key.[6][7]

This validates the core architectural claim from the research: where possible, the system should discover candidates from official search surfaces and then verify identity from previews or structured metadata.

### 2. What must be tightened

Some research claims are too optimistic if interpreted as "production-ready today".

The main gaps are:

- `API exists` does not always mean `self-serve and practically usable for this project`.
- Some APIs are clearly partner/sales-gated.
- Some banks expose strong public search surfaces, but not enough coverage to safely conclude anything stronger than `NOT PROVEN` when no match is found.
- Some public UIs support reverse image search, but that still requires browser automation and creates brittleness.

Validated examples:

- Getty Images API is real, but official access is framed as agreement/test-account driven rather than instant self-serve.[8]
- Alamy API is real, but is explicitly partnership-oriented.[9]
- Pond5 API is real, but official access is positioned as partner integration rather than simple self-serve search for hobby scripts.[10]
- Depositphotos API exists, but official positioning is API program / partner-style integration, not an obviously open self-serve developer workflow.[11][12]
- Envato Market has an API, but that does not validate an equivalent public API for Envato Elements photo presence detection.[13][14]

So the research is useful as strategy, but not yet a finished implementation spec.

### 3. Correct product interpretation

Because false positives are unacceptable, `markphotomediaapprovalstatusauto` should not be a "portfolio scraper that tries to auto-approve from text". It should become a conservative evidence engine:

- `FOUND` only when evidence is strong
- `NOT FOUND` otherwise

That is materially safer than the current branch behavior.

## Practical design consequences

### 1. Portfolio pages are not enough

Public contributor portfolios are useful as candidate sources, but not as the only truth source.

Why:

- portfolio pages may not expose the full catalog
- they may lazy-load or paginate unpredictably
- they may omit assets that are publicly searchable elsewhere
- they are often less stable than search APIs or search UIs

For several banks, official documentation points to stronger search surfaces than portfolio scraping:

- Adobe Stock Search API[1]
- Shutterstock search and API search[3][4]
- 123RF API search[5]
- Freepik stock content API[6][7]
- Vecteezy API search and filtering[15]
- Storyblocks API with test keys and search access[16]

Conclusion:

- Portfolio enumeration is a fallback candidate source.
- It should not be the primary basis for any explicit negative conclusion.

### 2. Verification must be preview-centric

For a `FOUND` decision, the safest generally available evidence is:

1. preview or thumbnail similarity
2. contributor identity match, when exposed
3. dimensions / aspect ratio consistency
4. asset ID match, when known or recoverable
5. text only as a weak supporting signal

This is strongly supported by the validated sources:

- Adobe returns search results via API and supports similarity-oriented search.[1][2]
- 123RF returns `id`, `link_image`, and optional `width` / `height` in search responses.[5]
- Getty describes search, metadata, reverse image search, and file sizes through API integration.[8]
- PIXTA publicly exposes image search and item pages with an item number and author number.[17][18]
- Mostphotos public item pages expose a stable item ID, contributor name, and dimensions.[19]

Conclusion:

- the matcher should be image-first, not title-first
- title/description should remain ranking helpers, not approval proof

### 3. `NOT FOUND` is not the same thing as rejected

The research is still useful here, but the product should be stricter than the research's `ABSENT` framing.

Even where search is available, public search often has ranking, paging, filtering, or access limits. Official documentation itself often implies limited or agreement-scoped visibility:

- Shutterstock free API subscriptions see only a limited media library and only the first 100 responses.[3]
- Getty explicitly says API results are constrained by the content in your agreement.[8]
- Storyblocks test keys exist, but full functionality depends on becoming an API client.[16]

Therefore:

- `FOUND` can often be proven from one strong candidate
- failure to find a candidate does not prove rejection
- the only safe non-positive result for this script is `NOT FOUND`

## Recommended output model

`markphotomediaapprovalstatusauto` should move to:

- `FOUND`
- `NOT FOUND`

Suggested operational meaning:

- `FOUND`: high-confidence identity proof; safe to mark as live / `schváleno`
- `NOT FOUND`: no sufficiently strong evidence that the asset is customer-visible right now; do not change the media status

This aligns with the user's asymmetric risk tolerance and is safer than binary title matching.

## Technology choices by bank

The table below focuses on what the implementation should use for each bank, why, and whether API availability is actually validated.

| Bank | API availability validated? | Recommended candidate discovery | Recommended verification | Main technology | Why this stack |
|---|---|---|---|---|---|
| Shutterstock | Yes, official API with auth/subscription.[3][4] | API search first; public profile/search second | Preview similarity + contributor + dimensions | `httpx` for API, Playwright only as fallback | Official search exists; reverse image and metadata are stronger than portfolio scraping |
| Adobe Stock | Yes, official Stock Search API.[1][2] | Search API first; public author page / web similar-search second | Preview similarity + creator ID + dimensions | `httpx` first, Playwright for web similar-search fallback | Official search and similarity features make Adobe one of the best targets |
| Getty Images / iStock | Yes, official API exists but agreement/test-account oriented.[8] | API if access exists; otherwise public search UI | Preview similarity + dimensions + any exposed creator metadata | `httpx` if API access, Playwright otherwise | Good official surface exists, but self-serve access is weaker |
| Depositphotos | API program exists, but partner-style.[11][12] | Public web search or reverse-image UI first unless API access is granted | Preview similarity + contributor + dimensions | Playwright + image matching; `httpx` only with API access | API availability is not enough to assume usable self-serve integration |
| 123RF | Yes, official API docs with IDs and thumbnails.[5] | API search first | Preview similarity + ID + dimensions | `httpx` | One of the clearest fits for deterministic candidate retrieval |
| Pond5 | Yes, official API exists, but partner-oriented.[10][20] | API if available; public search/UI otherwise | Preview similarity + contributor/asset metadata | `httpx` with API, Playwright fallback | Strong long-term target, but practical access may still be gated |
| Dreamstime | No clear official public API docs found in current official sources; public site and contributor filtering are visible.[21][22][23] | Public search with contributor filter; public portfolio as secondary source | Preview similarity + contributor username + dimensions | Playwright + image matching | Viable via public web, but not validated as an easy API-first bank |
| Bigstock | No usable official public API docs validated; official help shows contributor-scoped search syntax.[24][25] | Public search with `contributor:` filter | Preview similarity + contributor + dimensions | Playwright + image matching | Public web appears usable; API status is too weakly evidenced |
| Alamy | Yes, official partner API exists.[9] | API if access exists; otherwise public search | Preview similarity + contributor search + dimensions | `httpx` with API, Playwright fallback | Partnership API is real, but web fallback remains necessary for many setups |
| Freepik | Yes, official self-serve API key and stock content API.[6][7] | API search first | Preview similarity + resource ID + contributor metadata if exposed | `httpx` | Excellent target for API-first implementation |
| Vecteezy | Yes, official API with free and paid plans.[15] | API search first | Preview similarity + resource metadata | `httpx` | Validated self-serve API means web scraping should not be primary |
| Storyblocks | Yes, official API with test keys, but client-oriented.[16] | API search first if keys available | Preview similarity + metadata | `httpx` | Clear API direction, but full production access is commercial |
| Envato | Envato Market API exists; no validated equivalent for Elements photo-presence detection.[13][14] | Public search/UI for Elements-like surfaces; Market API only where truly relevant | Preview similarity + author/item metadata | Mixed: `httpx` for Market API, Playwright for Elements/web | Must not overgeneralize Market API to all Envato stock-photo surfaces |
| PIXTA | No public API validated; public search-by-image and item pages are validated.[17][18] | Public text search and image search UI | Preview similarity + item number + author number | Playwright + image matching | Good public customer surface, but browser automation is required |
| Mostphotos | No public API validated; public item pages with IDs and contributor names are visible.[19] | Public web search/profile/item pages | Preview similarity + item ID + contributor + dimensions | Playwright + image matching | Searchable and inspectable, but not API-first |
| 500px | Officially discontinued free API; sales contact required for further usage.[26] | Public web only | Preview similarity with strict thresholds | Playwright + image matching | High-risk and low-priority bank |
| CanStockPhoto | Closed.[27] | None | None | None | Do not invest |

## Bank-by-bank implementation table

This is the condensed implementation view for the actual script design.

| Bank | Recommended approach | Core technologies | Why this is the right fit |
|---|---|---|---|
| Adobe Stock | API-first | `httpx`, preview downloader, `pHash`, `dHash`, optional `CLIP` | Official search API is strong and similarity-oriented search is documented.[1][2] This is one of the safest banks for `FOUND`. |
| Shutterstock | API-first, browser fallback | `httpx`, preview downloader, optional `Playwright` fallback | Official API search exists.[3][4] Search + preview verification is safer than relying on public portfolio crawling. |
| 123RF | API-first | `httpx`, thumbnail fetch from `link_image`, `pHash`, `dHash`, dimension checks | Official API exposes media IDs, thumbnail URLs, and dimensions directly.[5] |
| Freepik | API-first | `httpx`, detail fetches, preview similarity | Official stock content API is documented and API-key based.[6][7] |
| Vecteezy | API-first | `httpx`, preview similarity | Official developer API is validated.[15] Scraping should not be primary. |
| Getty Images / iStock | API if available, otherwise web search | `httpx` when agreement access exists, otherwise `Playwright`, preview similarity | Official API exists, but access is more commercial/partner-like.[8] Public search remains useful fallback. |
| Alamy | API if available, otherwise web search | `httpx` with partner API, otherwise `Playwright`, preview similarity | Official API partnerships are validated.[9] Without access, public search becomes the practical route. |
| Pond5 | API if available, otherwise web search | `httpx`, `Playwright`, preview similarity, video-aware verification | Official API exists, but practical access can be gated.[10][20] Also needs a path for videos. |
| Depositphotos | Browser-first unless API access is granted | `Playwright`, preview downloader, `pHash`, `dHash` | API program exists, but practical self-serve usage is not clearly validated.[11][12] Public web/search is the safer implementation assumption. |
| Dreamstime | Browser-first | `Playwright`, contributor-filtered search, preview similarity | Current validated official surfaces are public search and contributor-filtered web flows, not a clearly usable self-serve API.[21][22][23] |
| Bigstock | Browser-first | `Playwright`, contributor-filtered search, preview similarity | Official evidence is stronger for contributor-scoped web search than for a current usable developer API.[24][25] |
| Storyblocks | API-first if keys exist, otherwise limited fallback | `httpx`, preview similarity, optional `Playwright` fallback | Official API is real and test keys are documented, but it remains client/business oriented.[16] |
| Envato | Mixed, surface-specific | `httpx` for Market API where relevant, `Playwright` for public web search, preview similarity | Must not overgeneralize Market API to Elements or all stock-photo surfaces.[13][14] |
| PIXTA | Browser-first | `Playwright`, image-search UI automation, item-number extraction, preview similarity | Public search-by-image and item pages are validated; no public API was validated.[17][18] |
| Mostphotos | Browser-first | `Playwright`, item/profile extraction, preview similarity | Public item pages expose IDs, contributor names, and dimensions.[19] That is enough for a web-first adapter. |
| 500px | Low-priority web fallback only | `Playwright`, strict image matching | Free API is discontinued.[26] Web-only support is possible but should stay low priority. |
| CanStockPhoto | Do not implement | none | The service is closed.[27] |

## What having a contributor account changes at each bank

Having a contributor account is useful, but its effect is narrower than it may first appear. In almost all cases, it helps with identity, stable portfolio URL discovery, and sometimes API application/access. It does **not** by itself make internal approval states a valid source of truth for this script, because the script's target is customer-visible availability.

General rule:

- contributor access may help you configure and stabilize the adapter
- customer-side evidence must still drive `FOUND`
- failing to find an item must still remain only `NOT FOUND`

### Shutterstock

- Contributor account helps because Shutterstock explicitly connects contributor portfolio management with content published on the customer website.[28][29]
- It also helps because the official developer platform requires a Shutterstock account and app registration for API use.[3][4]
- Practical effect:
  - short term: contributor account gives correct public identity and profile inputs
  - long term: contributor account gives a realistic path to API-backed search
- It does **not** make contributor-internal moderation state usable as proof for this script.

### Adobe Stock

- Contributor account helps because public contributor profiles exist and contributor identity can be aligned with customer-side search results.[30]
- Adobe's API itself is official and documented independently of contributor status, but contributor identity improves contributor-constrained search strategies.[1][2]
- Practical effect:
  - short term: author page and creator identity become much easier to anchor
  - long term: API-first remains the best path

### Getty Images / iStock

- Contributor access is less transformative than on some other banks.
- The main bottleneck is API agreement/access rather than contributor ownership alone.[8]
- Practical effect:
  - contributor account can help confirm naming, public presence, and known author metadata
  - it does not remove the need for API agreement or browser-based customer search fallback

### Depositphotos

- Contributor access helps identify exact public portfolio/public-author surfaces and reduces ambiguity around contributor identity.
- Official API availability still appears program/partner oriented rather than obviously open self-serve.[11][12]
- Practical effect:
  - short term: better browser-first configuration
  - long term: contributor access may help initiate official API program discussions, but does not itself validate API usability today

### 123RF

- Contributor access helps by anchoring the contributor identity and any author-related filtering strategy.
- But the bigger win is that 123RF already has documented API search surfaces with IDs and preview links.[5]
- Practical effect:
  - contributor account is helpful but not the core enabler
  - API-first is still the correct design

### Pond5

- Contributor access helps because Pond5 has contributor/artist-facing identity surfaces and also supports video, where correct account alignment matters operationally.
- API existence is validated, but practical usage can still depend on commercial access.[10][20]
- Practical effect:
  - short term: contributor identity helps browser-side search/profile narrowing
  - long term: contributor account may help with API access discussions, but browser fallback remains necessary unless access is actually granted

### Dreamstime

- Contributor access matters materially here.
- Dreamstime has an official API program, but it appears request-based / access-gated rather than publicly open with immediate developer self-service.[31]
- Dreamstime public advanced search visibly supports `Only from Contributor(s)` filtering.[32][33]
- Public contributor profile pages also exist.[34]
- Practical effect:
  - short term: best path is browser-first using public advanced search plus contributor filter
  - medium/long term: contributor account gives a realistic path to formally request API access
- This is one of the clearest cases where contributor ownership changes the practical opportunity, but not enough to justify assuming API-first immediately.

### Bigstock

- Contributor access helps mostly with exact contributor naming and public portfolio/search narrowing.
- The strongest validated official signal is still contributor-scoped public search, not a clearly usable public API.[24][25]
- Practical effect:
  - browser-first remains the right near-term strategy
  - contributor account improves search precision, but does not fundamentally change the technical stack

### Alamy

- Contributor access can help identify the exact customer-side contributor naming needed for author-based search.
- But API access is officially partnership-driven.[9]
- Practical effect:
  - contributor account helps with public search filters and identity confirmation
  - it does not replace the need for API partnership if you want API-first

### Freepik

- Contributor account is less central here because the strongest validated path is the official API key workflow.[6][7]
- It still helps map any contributor identity exposed on public resource pages, where relevant.
- Practical effect:
  - API-first remains primary regardless
  - contributor account is supportive, not decisive

### Vecteezy

- Contributor account may help with account-specific identity and public-facing author/profile confirmation.
- The stronger fact is that a developer API exists with access tiers.[15]
- Practical effect:
  - contributor account helps configuration
  - API-first still dominates the design

### Storyblocks

- Contributor access may help on the content-owner side, but the main gating factor is API/client access, not contributor ownership alone.[16]
- Practical effect:
  - contributor account is secondary
  - this remains API-if-available, otherwise weak web fallback

### Envato

- Contributor access may help clarify whether the relevant content lives on a Market surface or an Elements-like customer surface.
- That distinction matters because validated official API support is much clearer for Market than for Elements.[13][14]
- Practical effect:
  - contributor account improves source mapping and manual interpretation
  - it does not eliminate the need for browser-based customer-side validation on many Envato surfaces

### PIXTA

- Contributor access is useful because public item pages expose item and author numbers, and contributor ownership makes author identity easier to anchor.[17][18]
- No public API was validated.
- Practical effect:
  - browser-first remains correct
  - contributor account improves precision substantially

### Mostphotos

- Contributor account helps identify the exact public profile and contributor naming used on item pages.[19]
- No public API was validated.
- Practical effect:
  - browser-first remains correct
  - contributor access helps profile-based narrowing but does not change the stack

### 500px

- Contributor access helps mostly for identity and profile awareness.
- The main limitation is still that the free API is discontinued.[26]
- Practical effect:
  - contributor account does not rescue this from low priority

### CanStockPhoto

- Contributor access is irrelevant because the service is closed.[27]

## Updated practical classification with contributor accounts assumed

Assuming you already have contributor accounts on all banks, the practical classification becomes:

- Strongest API-first targets: Adobe Stock, Shutterstock, 123RF, Freepik, Vecteezy
- API-if-access-is-granted: Getty/iStock, Alamy, Pond5, Storyblocks, Depositphotos
- Browser-first but materially improved by contributor identity: Dreamstime, Bigstock, PIXTA, Mostphotos
- Mixed/unclear surface mapping: Envato
- Low priority even with contributor account: 500px
- Do not implement: CanStockPhoto

## Interface features worth reusing from other Codex branches

After reviewing the existing `codex/*` branch patterns in this repository, only a small subset of the interface unification work should be reused in `markphotomediaapprovalstatusauto`.

These should be adopted:

- `--banks`
- `--dry-run`
- report export (`--report-dir` or equivalent)

These should **not** be adopted here:

- GUI-style preview/interactive modes
- batch action semantics from manual tools
- anything that implies manual review inside the automatic pipeline
- any interface that suggests the script can set `zamítnuto`

### `--banks`

Why to reuse it:

- this is a natural fit for per-bank rollout and debugging
- it aligns with existing Codex branch work around script-level bank filtering
- it allows safer staged validation before broader runs

Recommended behavior:

- accept a comma-separated bank list
- process only those banks
- preserve the same bank-name normalization rules as the rest of the repository

### `--dry-run`

Why to reuse it:

- this script is high-risk because a wrong positive write is unacceptable
- a full read/verify/audit run without CSV writes is operationally necessary

Recommended behavior:

- execute full candidate discovery and verification
- produce logs and report output
- do not write `schváleno` back to CSV

### Report export

Why to reuse it:

- automatic customer-side detection requires an audit trail
- the result should be inspectable outside logs
- this is especially important for `NOT FOUND`, because it means only "not proven"

Recommended report content:

- local file
- bank
- result (`FOUND` / `NOT FOUND`)
- matched URL if any
- matched asset ID if any
- contributor match signal
- preview similarity score
- dimension/aspect check
- textual explanation / reason code

This should be emitted regardless of whether `--dry-run` is enabled, because it is useful both for rehearsal and for real runs.

## What each bank will likely require technically

### Tier A: API-first banks

These are the banks where production logic should start with structured HTTP calls.

#### Adobe Stock

Use:

- `httpx` / `requests`
- preview downloader
- pHash / dHash
- optional CLIP embedding verifier

Why:

- official Search API supports search/filter/pagination[1]
- official docs support search by creator/asset/similarity modes[2]
- this is one of the strongest banks for evidence-based `FOUND`

#### Shutterstock

Use:

- `httpx`
- preview downloader
- pHash / dHash
- optional Playwright fallback for web-only diagnostics

Why:

- official API search exists, but authenticated subscriptions matter[3][4]
- HTTP is the stable path; browser should not be primary unless API access is missing

#### 123RF

Use:

- `httpx`
- thumbnail downloader from `link_image`
- pHash / dHash
- aspect-ratio checks

Why:

- official search response includes exactly the metadata needed for candidate verification[5]

#### Freepik

Use:

- `httpx`
- ID/detail fetches
- preview similarity

Why:

- official API key workflow is documented and self-serve[6][7]

#### Vecteezy

Use:

- `httpx`
- preview similarity

Why:

- official developers site documents an API product with free and paid access tiers.[15]

### Tier B: API-if-available, otherwise web-search

#### Getty Images / iStock

Use:

- `httpx` if API agreement/test account exists
- otherwise Playwright for search UI
- preview similarity

Why:

- official API is real, but access is agreement-based[8]
- design must tolerate not having API access everywhere

#### Alamy

Use:

- `httpx` if API partnership access exists
- otherwise Playwright for public search flows
- preview similarity

Why:

- official API is partner-centric[9]

#### Pond5

Use:

- `httpx` if API access exists
- Playwright fallback for customer-side search
- preview similarity
- video-aware verification path for motion assets

Why:

- official API is validated[10][20]
- but production access may still be negotiated rather than instant self-serve

#### Storyblocks

Use:

- `httpx` with test keys/client access
- preview similarity

Why:

- official site explicitly offers test keys and API search access[16]
- still closer to business integration than unrestricted public search

### Tier C: browser-first banks

These are the banks where the validated evidence points more to public search/UI than to reliable self-serve APIs.

#### Dreamstime

Use:

- Playwright
- preview downloader
- pHash / dHash
- contributor-filtered search

Why:

- official site clearly exposes public search and contributor filtering[21][22][23]
- no strong current self-serve API evidence was validated from official docs

#### Bigstock

Use:

- Playwright
- contributor-filtered search
- preview similarity

Why:

- official help content documents contributor-scoped search syntax (`contributor:theirname`)[24]
- no validated current public developer API documentation was found from official sources

#### PIXTA

Use:

- Playwright
- image-search UI automation
- preview similarity
- item-number extraction

Why:

- official public site exposes search by image and item pages with stable item numbers and author numbers[17][18]

#### Mostphotos

Use:

- Playwright
- item-page extraction
- preview similarity

Why:

- public item pages expose stable IDs, contributor names, and sizes[19]
- no validated public API path found

#### 500px

Use:

- optional low-priority Playwright web search only
- very strict similarity thresholds

Why:

- official support states free API access was discontinued in 2018[26]
- scraping risk is higher and confidence lower

### Tier D: do not implement

#### CanStockPhoto

Use:

- none

Why:

- official closure notice makes integration pointless.[27]

## Recommended evidence model

### For `FOUND`

Require at least:

- strong image similarity
- plus one strong structural signal:
  - contributor identity
  - stable asset ID
  - dimensions / aspect ratio

Safe examples:

- API returns a candidate with stable ID and thumbnail, and the preview matches the local file strongly.
- Public search returns one candidate from the known contributor, and preview similarity is very high.

### For `NOT FOUND`

This bucket includes all cases where the script does not have enough evidence to assert customer-visible availability. Examples:

- no candidate found
- candidate found but similarity is too weak
- multiple near-duplicate candidates remain ambiguous
- API access is missing and web evidence is incomplete
- public search may be incomplete or non-exhaustive
- the item might still be in moderation, shadow-delayed in indexing, or simply not discovered by the current run

Operational rule:

- `NOT FOUND` must never set `zamítnuto`
- `NOT FOUND` must never infer rejection
- `NOT FOUND` means only "we did not find sufficient proof of customer-visible availability right now"

## Recommended implementation stack

At a system level, the most justified stack is:

- `httpx` for official APIs and predictable HTTP search
- `Playwright` only where browser automation is genuinely necessary
- preview image download/cache layer
- image verification:
  - pHash
  - dHash
  - optional SSIM
  - optional CLIP embeddings for hard cases
- explicit audit storage:
  - candidate URL
  - candidate ID
  - preview bytes or hash
  - similarity metrics
  - contributor/dimension signals
  - final decision reason

That stack is justified because many validated banks expose either:

- structured metadata and previews directly through API, or
- stable public previews and item pages that can be browser-driven when API is missing.

## Final recommendation for the branch

The current branch should not continue to optimize title-based public-portfolio crawling as its primary strategy.

It should be reworked into:

1. bank-specific candidate discovery adapters
2. a common preview-verification engine
3. a conservative proof layer
4. per-bank validation against known `schváleno` / `zamítnuto` records

Short version:

- keep portfolio crawling only as one candidate source
- move approval proof to image-backed evidence
- prefer API-first where official search access is validated
- never map "not found" to `zamítnuto`
- optimize for "no false positives", not for maximum automation rate

## Sources

[1] Adobe Stock Search API reference: https://developer.adobe.com/stock/docs/api/11-search-reference/  
[2] Adobe Stock "Search for assets": https://developer.adobe.com/stock/docs/getting-started/apps/05-search-for-assets/  
[3] Shutterstock Getting Started / auth and subscriptions: https://www.shutterstock.com/developers/documentation/getting-started  
[4] Shutterstock Authentication: https://www.shutterstock.com/developers/documentation/authentication  
[5] 123RF API documentation: https://www.123rfapis.com/documentation/  
[6] Freepik authentication: https://docs.freepik.com/authentication  
[7] Freepik stock content API: https://docs.freepik.com/api-reference/resources/stock-content  
[8] Getty Images API official page: https://www.gettyimages.ie/api  
[9] Alamy API partnerships: https://www.alamy.com/api-partnerships/  
[10] Pond5 API landing: https://www.pond5.com/api/  
[11] Depositphotos API program signup: https://depositphotos.com/api-program/signup.html  
[12] Depositphotos API agreement: https://depositphotos.com/api-agreement.html  
[13] Envato Market API terms: https://help.market.envato.com/hc/en-us/articles/42875085863705-Envato-Market-API-Terms  
[14] Envato Market user terms (API mention): https://help.market.envato.com/hc/en-us/articles/41383541904281-Envato-Market-User-Terms  
[15] Vecteezy developers/API: https://www.vecteezy.com/developers  
[16] Storyblocks API: https://www.storyblocks.com/resources/business-solutions/api  
[17] PIXTA public search and image search: https://www.pixtastock.com/  
[18] PIXTA public item page with item number / author number example: https://www.pixtastock.com/illustration/110069049  
[19] Mostphotos public item page example: https://www.mostphotos.com/en-us/2253208/red-cat-breed-selkirk-rex  
[20] Pond5 older API reference: https://www.pond5.com/index.php?page=api_ref_doc  
[21] Dreamstime homepage / public search: https://www.dreamstime.com/  
[22] Dreamstime contributor portfolio example: https://www.dreamstime.com/imagecollect_info  
[23] Dreamstime search UI with "Only from Contributor(s)" filter: https://www.dreamstime.com/photos-images/searching-tool.html  
[24] Bigstock official help - search within a portfolio / contributor syntax: https://www.bigstockphoto.com/help/en/articles/10439121-technical  
[25] Bigstock site footer confirms "API & Partners" exists, but no validated public current API docs were found from official sources: https://www.bigstockphoto.com/login/  
[26] 500px API discontinued: https://support.500px.com/hc/en-us/articles/360002435653-API  
[27] Can Stock Photo closure notice: https://www.canstockphoto.com/illustration/crunch-time.html  
