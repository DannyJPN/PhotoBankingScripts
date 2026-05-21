"""Pond5 discovery adapter.

Strategy: crawl contributor portfolio page once (Playwright + persistent browser profile),
extract all (asset_id, preview_url) pairs directly from rendered HTML, then use those
CDN URLs for pHash verification.

Real CDN pattern discovered: https://images.pond5.com/{slug}-photo-{ID}_iconl_nowm.jpeg
Portfolio URL read from public_portfolios.json: https://www.pond5.com/artist/{name}?tab=photo&...

Navigation: Pond5 portfolio is a SPA.  Direct URL navigation (goto pp=N) causes the app to
re-initialise and return the same content after ~page 43.  The correct approach is to navigate
to page 1 once and then click the ``js-paginationV2Next`` button for each subsequent page —
exactly as a real user would.  This reaches all pages without cycling.
"""

import csv
import datetime
import logging
import math
import os
import random
import re
import time
import urllib.parse
from typing import List, Optional, Set, Tuple

from markphotomediaapprovalstatusautolib.discovery.base import BankDiscoveryAdapter
from markphotomediaapprovalstatusautolib.models import Candidate, PhotoRecord


def build_search_vocabulary(rows: List[dict], max_depth: int = 3) -> Set[str]:
    """Build a set of word-start prefixes (length 1..*max_depth*) from photo metadata.

    Extracts every alphabetic word from 'Název', 'Popis', and 'Klíčová slova' fields of
    every row, then records prefixes of length 1 to min(word_length, max_depth).
    The result is passed to ``crawl_pond5_portfolio`` as *search_vocabulary* so Phase 2
    only searches letter combinations that are a prefix of at least one word in the
    contributor's metadata — e.g. "abs" is searched only if a word like "abstract" or
    "absolute" exists; "bst" (mid-word) is never searched.

    :param rows: List of CSV row dicts (PhotoMedia rows).
    :param max_depth: Maximum prefix length (default: 3, matching ``_PREFIX_MAX_DEPTH``).
    :return: Set of lowercase word-start prefix strings present in the metadata.
    """
    _word_re = re.compile(r"[a-z]+")
    vocab: Set[str] = set()
    for row in rows:
        text = " ".join(filter(None, [
            row.get("Název") or "",
            row.get("Popis") or "",
            row.get("Klíčová slova") or "",
        ])).lower()
        for word in _word_re.findall(text):
            for length in range(1, min(len(word), max_depth) + 1):
                vocab.add(word[:length])
    return vocab

# Full CDN preview URL with embedded asset ID — no watermark variant.
# ID field captures 6-12 digits to handle both legacy short IDs and future long IDs.
_CDN_URL_RE = re.compile(r'(https://images\.pond5\.com/[^\s"\'<]+?-(\d{6,12})_iconl_nowm\.jpeg)')

# Contributor name extracted from URL like pond5.com/artist/dannyjpn
_CONTRIBUTOR_RE = re.compile(r'/artist/([^/?&]+)')

# Sort orders to try in sequence.  Pond5 cycles duplicate content after ~43 pages for any
# one sort order; cycling through several sb= values gives access to the full portfolio.
# Valid Pond5 sb= values: 6=newest, 1=best match, 8=popular, 4=price low→high, 3=price high→low
_SORT_ORDERS = ["6", "1", "8", "4", "3"]

_PAGE_SIZE = 48   # Pond5 portfolio shows 48 assets per page
_PAGE_WAIT_MS = 4000  # ms to wait after each page navigation before extracting HTML
_NEXT_BTN_SELECTOR = ".js-paginationV2Next"  # CSS selector for the Next page button
_MAX_CONSECUTIVE_ZERO_PAGES = 5        # Stop a sort/keyword pass after N pages with no new assets
_RECOVERY_MAX_RETRIES = 1              # Max automatic DataDome recovery attempts per pass
_PREFIX_INTER_REQUEST_DELAY = (2.0, 5.0)  # Random sleep (seconds) between letter-prefix requests
_PREFIX_LIMIT = 2048                   # Pond5 server-side result cap; subdivide prefix when expected_total exceeds this
_PREFIX_MAX_DEPTH = 3                  # Maximum prefix length (a → ab → abc)


def extract_contributor_name(portfolio_url: str) -> str:
    """Extract contributor username from a Pond5 portfolio URL.

    :param portfolio_url: Full portfolio URL, e.g. ``https://www.pond5.com/artist/dannyjpn?tab=photo``.
    :return: Contributor username string, or empty string if not found.
    """
    match = _CONTRIBUTOR_RE.search(portfolio_url)
    return match.group(1) if match else ""


def _extract_assets_from_html(html: str) -> List[Tuple[int, str]]:
    """Extract (asset_id, cdn_preview_url) pairs from rendered Pond5 portfolio HTML.

    :param html: Fully rendered HTML content of the portfolio page.
    :return: List of (asset_id, cdn_url) tuples — duplicates within the page deduplicated.
    """
    seen_ids: Set[int] = set()
    assets: List[Tuple[int, str]] = []
    for cdn_url, asset_id_str in _CDN_URL_RE.findall(html):
        asset_id = int(asset_id_str)
        if asset_id not in seen_ids:
            seen_ids.add(asset_id)
            assets.append((asset_id, cdn_url))
    return assets


_TOTAL_COUNT_RE = re.compile(r"(\d[\d,]+)\s+photo")


def _build_search_url(portfolio_url: str, keyword: str) -> str:
    """Build a portfolio URL filtered by *keyword* using Pond5's ``search=`` parameter.

    Keyword searches return only photos matching that keyword, keeping results well
    below the ~2048-asset sort-order ceiling and avoiding cycling.

    :param portfolio_url: Base portfolio URL.
    :param keyword: Search term to filter by (e.g. ``"deer"``).
    :return: URL with ``search={keyword}`` set and ``pp`` removed (will be set per-page).
    """
    parsed = urllib.parse.urlparse(portfolio_url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    params["search"] = [keyword]
    params.pop("pp", None)
    new_query = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def _build_page_url(portfolio_url: str, page: int, sb: Optional[str] = None) -> str:
    """Build a page URL with ``pp=page`` and an optional ``sb=`` sort override.

    :param portfolio_url: Base portfolio URL (may already contain ``pp=1`` and ``sb=``).
    :param page: 1-based page number.
    :param sb: Sort order value to set; when None the existing ``sb=`` is kept as-is.
    :return: URL with ``pp={page}`` (and optionally ``sb={sb}``) set.
    """
    parsed = urllib.parse.urlparse(portfolio_url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    params["pp"] = [str(page)]
    if sb is not None:
        params["sb"] = [sb]
    # Keep tab=photo — removing it causes Pond5 to show all media types
    new_query = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def _open_browser_context(pw, profile_dir: Optional[str], headless: bool):
    """Open a Playwright browser context, using a persistent profile when available.

    :param pw: Active sync_playwright instance.
    :param profile_dir: Path to persistent Chromium profile, or None.
    :param headless: Run browser headless when True.
    :return: Playwright browser context object.
    """
    if profile_dir and os.path.isdir(profile_dir):
        return pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            locale="en-US",
            viewport={"width": 1920, "height": 1080},
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
    browser = pw.chromium.launch(headless=headless)
    return browser.new_context(locale="en-US", viewport={"width": 1920, "height": 1080})


def _recover_from_datadome(
    pw,
    portfolio_url: str,
    profile_dir: Optional[str],
    cooldown_seconds: int,
    captcha_timeout_seconds: int,
) -> bool:
    """Wait for Pond5 to cool down, then open a visible browser for manual CAPTCHA solving.

    Two-phase recovery:
    1. Sleep *cooldown_seconds* so the server rate-limit resets.
    2. Open a visible browser (same persistent profile) and navigate to the portfolio.
       Wait up to *captcha_timeout_seconds* for the page to load — user can solve
       any CAPTCHA challenge shown during that window.

    Closing the visible context saves updated cookies back to the profile, so the next
    headless run benefits from the refreshed session.

    :param pw: Active sync_playwright instance.
    :param portfolio_url: URL to navigate to for the CAPTCHA challenge.
    :param profile_dir: Persistent Chromium profile directory.
    :param cooldown_seconds: Seconds to sleep before opening the visible browser.
    :param captcha_timeout_seconds: Max seconds to wait for the user to solve CAPTCHA.
    :return: True if the portfolio page loaded successfully, False on timeout.
    """
    logging.warning(
        "DataDome block — waiting %ds for Pond5 to cool down before recovery...",
        cooldown_seconds,
    )
    time.sleep(cooldown_seconds)

    logging.warning(
        "Opening visible browser for CAPTCHA solving (if needed). Timeout: %ds.",
        captcha_timeout_seconds,
    )
    ctx = _open_browser_context(pw, profile_dir, headless=False)
    page = ctx.new_page()
    try:
        try:
            page.goto(portfolio_url, timeout=30000)
        except Exception as exc:
            logging.warning("Navigation during recovery failed (continuing to wait): %s", exc)
        deadline = time.monotonic() + captcha_timeout_seconds
        while time.monotonic() < deadline:
            time.sleep(3)
            try:
                if len(page.content()) > 10000:
                    logging.info("Recovery successful — portfolio page loaded.")
                    return True
            except Exception:
                pass
        logging.error(
            "Recovery timeout after %ds — CAPTCHA not solved. "
            "Run: python save_bank_session.py --bank Pond5",
            captcha_timeout_seconds,
        )
        return False
    finally:
        ctx.close()


class PortfolioCache:
    """Kumulativní CSV cache pro Pond5 portfolio assety.

    Záznamy jsou permanentní — cache nikdy neodstraňuje existující položky, pouze přidává nové.
    Formát je čitelný bez speciálních nástrojů (CSV, UTF-8).
    """

    _COLUMNS = ["asset_id", "cdn_url", "first_seen"]

    def __init__(self, cache_path: str) -> None:
        """Inicializace cache.

        :param cache_path: Cesta k CSV souboru cache.
        """
        self._path = cache_path

    def load(self) -> List[Tuple[int, str]]:
        """Načte existující záznamy ze souboru.

        :return: Seznam (asset_id, cdn_url) párů; prázdný seznam pokud soubor neexistuje.
        """
        if not os.path.isfile(self._path):
            return []
        assets: List[Tuple[int, str]] = []
        try:
            with open(self._path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    try:
                        assets.append((int(row["asset_id"]), row["cdn_url"]))
                    except (KeyError, ValueError):
                        pass
        except Exception as exc:
            logging.warning("PortfolioCache: failed to load %s: %s", self._path, exc)
        logging.info("PortfolioCache: loaded %d assets from %s", len(assets), self._path)
        return assets

    def save(self, assets: List[Tuple[int, str]]) -> None:
        """Uloží kompletní seznam assetů — provede merge s existujícím obsahem.

        Existující záznamy, které nejsou v *assets*, jsou zachovány (kumulativní chování).

        :param assets: Aktuální seznam (asset_id, cdn_url) párů.
        """
        existing = {asset_id: cdn_url for asset_id, cdn_url in self.load()}
        today = datetime.date.today().isoformat()
        # Merge: existující + nové
        merged: dict = dict(existing)
        for asset_id, cdn_url in assets:
            if asset_id not in merged:
                merged[asset_id] = cdn_url
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
            with open(self._path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=self._COLUMNS)
                writer.writeheader()
                for asset_id, cdn_url in sorted(merged.items()):
                    writer.writerow({"asset_id": asset_id, "cdn_url": cdn_url, "first_seen": today})
            logging.info("PortfolioCache: saved %d assets to %s", len(merged), self._path)
        except Exception as exc:
            logging.error("PortfolioCache: failed to save %s: %s", self._path, exc)

    def known_ids(self) -> Set[int]:
        """Vrátí množinu již uložených asset_id.

        :return: Set asset_id z cache.
        """
        return {asset_id for asset_id, _ in self.load()}


def _crawl_sort_pass(
    browser_page,
    portfolio_url: str,
    sb: str,
    seen_ids: Set[int],
    assets: List[Tuple[int, str]],
    max_pages: int,
) -> Tuple[int, Optional[int], bool]:
    """Crawl one sort pass using click-based navigation, updating *assets* and *seen_ids* in place.

    Navigates to page 1 via URL (correct SPA initialisation), then advances through pages by
    clicking the ``js-paginationV2Next`` button — identical to real user behaviour.  Direct
    URL navigation to pp=N>43 causes the SPA to re-initialise and return cycling content.

    :param browser_page: Active Playwright page object.
    :param portfolio_url: Base portfolio URL.
    :param sb: Sort order value (Pond5 ``sb=`` parameter).
    :param seen_ids: Global set of already-collected asset IDs (updated in place).
    :param assets: Global list of collected (asset_id, cdn_url) pairs (updated in place).
    :param max_pages: Hard upper limit on pages per pass.
    :return: (new_count, expected_total, datadome_hit) — new assets added this pass,
        total portfolio size (or None if never found), and whether a DataDome block occurred.
    """
    total_pages: Optional[int] = None
    expected_total: Optional[int] = None
    new_count = 0
    datadome_hit = False

    # Navigate to page 1 — direct URL is correct here (SPA initialises from page 1)
    page1_url = _build_page_url(portfolio_url, 1, sb=sb)
    logging.info("[sb=%s] Navigating to page 1: %s", sb, page1_url)
    try:
        browser_page.goto(page1_url, timeout=30000)
        browser_page.wait_for_timeout(_PAGE_WAIT_MS)
    except Exception as exc:
        logging.error("[sb=%s] Failed to navigate to page 1: %s — stopping pass", sb, exc)
        return new_count, expected_total, datadome_hit

    consecutive_zero = 0
    for page_num in range(1, max_pages + 1):
        html = browser_page.content()
        if len(html) < 10000:
            logging.error(
                "Pond5 page %d too short (%d bytes) — DataDome block.",
                page_num,
                len(html),
            )
            datadome_hit = True
            break

        if expected_total is None:
            m = _TOTAL_COUNT_RE.search(html)
            if m:
                expected_total = int(m.group(1).replace(",", ""))
                total_pages = math.ceil(expected_total / _PAGE_SIZE)
                logging.info(
                    "[sb=%s] Total portfolio: %d photos -> %d pages",
                    sb,
                    expected_total,
                    total_pages,
                )

        page_assets = _extract_assets_from_html(html)
        new_this_page = 0
        for asset_id, cdn_url in page_assets:
            if asset_id not in seen_ids:
                seen_ids.add(asset_id)
                assets.append((asset_id, cdn_url))
                new_count += 1
                new_this_page += 1

        logging.info(
            "[sb=%s] Page %d/%s: extracted=%d, new=%d (total unique: %d)",
            sb,
            page_num,
            total_pages or "?",
            len(page_assets),
            new_this_page,
            len(assets),
        )

        if new_this_page == 0:
            consecutive_zero += 1
            if consecutive_zero >= _MAX_CONSECUTIVE_ZERO_PAGES:
                logging.info(
                    "[sb=%s] %d consecutive pages with 0 new assets — stopping pass",
                    sb,
                    consecutive_zero,
                )
                break
        else:
            consecutive_zero = 0

        if total_pages is not None and page_num >= total_pages:
            logging.info("[sb=%s] Reached final page (%d)", sb, total_pages)
            break

        # Click Next button — simulates real user; avoids SPA re-initialisation on direct goto()
        next_btn = browser_page.locator(_NEXT_BTN_SELECTOR)
        if next_btn.count() == 0:
            logging.info("[sb=%s] Next button not found on page %d — stopping", sb, page_num)
            break

        btn_classes = next_btn.get_attribute("class") or ""
        if "is-disabled" in btn_classes:
            logging.info("[sb=%s] Next button disabled on page %d — last page reached", sb, page_num)
            break

        url_before = browser_page.url
        next_btn.scroll_into_view_if_needed()
        try:
            # Normal click works for pages where there is no overlay
            next_btn.click(timeout=5000)
        except Exception as exc:
            if "TargetClosedError" in type(exc).__name__ or "Target page" in str(exc):
                logging.error("[sb=%s] Browser was closed — stopping crawl", sb)
                return new_count, expected_total
            # Spinner/overlay intercepts pointer events — fall back to JS click which bypasses it
            logging.info("[sb=%s] Pointer intercepted on page %d, falling back to JS click", sb, page_num)
            try:
                browser_page.evaluate("document.querySelector('.js-paginationV2Next').click()")
            except Exception as js_exc:
                if "TargetClosedError" in type(js_exc).__name__ or "Target page" in str(js_exc):
                    logging.error("[sb=%s] Browser was closed during JS click — stopping crawl", sb)
                    return new_count, expected_total
                raise
        browser_page.wait_for_timeout(_PAGE_WAIT_MS)
        url_after = browser_page.url
        logging.info(
            "[sb=%s] Page %d -> pp=%s (url changed: %s)",
            sb,
            page_num,
            url_after.split("pp=")[-1].split("&")[0] if "pp=" in url_after else "?",
            url_before != url_after,
        )

    return new_count, expected_total, datadome_hit


def _crawl_letter_prefix_phase(
    pw,
    portfolio_url: str,
    profile_dir: Optional[str],
    headless: bool,
    seen_ids: Set[int],
    assets: List[Tuple[int, str]],
    max_pages: int,
    datadome_cooldown: int,
    captcha_timeout: int,
    prefix: str = "",
    depth: int = 0,
    search_vocabulary: Optional[Set[str]] = None,
    cache: Optional["PortfolioCache"] = None,
    _state: Optional[List] = None,
) -> Tuple[int, bool]:
    """Rekurzivní letter-prefix crawl pokrývající assety mimo dosah sort passů.

    Pro každé písmeno abecedy sestaví ``search=<prefix><letter>`` URL a zavolá
    ``_crawl_sort_pass()``.  Pokud Pond5 hlásí ``expected_total > _PREFIX_LIMIT``
    (server vrátí jen prvních 2 048 výsledků), rekurzivně volá sebe s delším prefixem —
    až do ``_PREFIX_MAX_DEPTH``.

    Příklad: "a" → 3 200 výsledků → rekurzivně "aa", "ab", ..., "az".

    Celá Phase 2 (včetně všech rekurzivních subdivizí) sdílí jeden browser kontext
    předaný přes *_state* = ``[ctx, browser_page]``.  Kontext se zavírá a otevírá
    pouze při DataDome recovery — nikoliv mezi písmeny nebo při subdivizi.

    :param pw: Aktivní sync_playwright instance.
    :param portfolio_url: Základní URL portfolia.
    :param profile_dir: Cesta k persistentnímu Chromium profilu.
    :param headless: Bezobrazovkový režim.
    :param seen_ids: Globální množina již nalezených asset_id (modifikována in-place).
    :param assets: Globální seznam (asset_id, cdn_url) párů (modifikován in-place).
    :param max_pages: Maximální počet stránek na jeden pass.
    :param datadome_cooldown: Sekundy čekání po DataDome bloku.
    :param captcha_timeout: Maximální sekundy čekání na vyřešení CAPTCHA.
    :param prefix: Aktuální textový prefix (prázdný na začátku).
    :param depth: Aktuální hloubka rekurze (0 = jednopísmenné hledání).
    :param search_vocabulary: Množina word-start prefixů ze slov metadat hledaných fotek.
        Je-li None, prohledají se všechna písmena abecedy.
    :param cache: PortfolioCache instance pro průběžné ukládání po každém prefixu.
    :param _state: Interní mutable list ``[ctx, browser_page]`` sdílený napříč rekurzí.
        Volající předává None (top-level); subdivize předávají stávající state.
    :return: (total_new, any_datadome_hit)
    """
    import string

    total_new = 0
    any_datadome_hit = False
    owns_state = _state is None

    if owns_state:
        ctx = _open_browser_context(pw, profile_dir, headless)
        browser_page = ctx.new_page()
        _state = [ctx, browser_page]

    try:
        for letter in string.ascii_lowercase:
            search_term = prefix + letter
            if search_vocabulary is not None and search_term not in search_vocabulary:
                logging.debug("Letter prefix '%s': not in vocabulary — skipping", search_term)
                continue
            delay = random.uniform(*_PREFIX_INTER_REQUEST_DELAY)
            logging.debug("Letter-prefix inter-request delay: %.1fs", delay)
            time.sleep(delay)

            kw_url = _build_search_url(portfolio_url, search_term)
            logging.info("Letter prefix '%s' (depth=%d): %s", search_term, depth, kw_url)

            for attempt in range(_RECOVERY_MAX_RETRIES + 1):
                ctx, browser_page = _state
                new_count, expected_total, datadome_hit = _crawl_sort_pass(
                    browser_page, kw_url, "6", seen_ids, assets, max_pages
                )
                if not datadome_hit:
                    break
                if attempt < _RECOVERY_MAX_RETRIES:
                    ctx.close()
                    recovered = _recover_from_datadome(
                        pw, portfolio_url, profile_dir, datadome_cooldown, captcha_timeout
                    )
                    ctx = _open_browser_context(pw, profile_dir, headless)
                    browser_page = ctx.new_page()
                    _state[0], _state[1] = ctx, browser_page
                    if not recovered:
                        logging.warning("Letter prefix '%s': recovery failed — skipping", search_term)
                        any_datadome_hit = True
                        break
                else:
                    logging.warning("Letter prefix '%s': still blocked after recovery — skipping", search_term)
                    any_datadome_hit = True

            if datadome_hit:
                continue

            total_new += new_count
            logging.info(
                "Letter prefix '%s' done: +%d new (unique total: %d)",
                search_term, new_count, len(assets),
            )

            if cache is not None and new_count > 0:
                cache.save(assets)
                logging.debug("Cache saved after prefix '%s' (%d total assets)", search_term, len(assets))

            # Subdivide if Pond5 reports more results than the server-side cap —
            # pass the shared _state so no new browser window is opened
            if (
                expected_total is not None
                and expected_total > _PREFIX_LIMIT
                and depth < _PREFIX_MAX_DEPTH - 1
            ):
                logging.info(
                    "Letter prefix '%s': expected_total=%d > %d — subdividing to depth %d",
                    search_term, expected_total, _PREFIX_LIMIT, depth + 1,
                )
                sub_new, sub_hit = _crawl_letter_prefix_phase(
                    pw, portfolio_url, profile_dir, headless,
                    seen_ids, assets, max_pages,
                    datadome_cooldown, captcha_timeout,
                    prefix=search_term, depth=depth + 1,
                    search_vocabulary=search_vocabulary,
                    cache=cache,
                    _state=_state,
                )
                total_new += sub_new
                if sub_hit:
                    any_datadome_hit = True

    finally:
        if owns_state:
            ctx, browser_page = _state
            try:
                ctx.close()
            except Exception:
                pass

    return total_new, any_datadome_hit


def crawl_pond5_portfolio(
    portfolio_url: str,
    headless: bool = False,
    profile_dir: Optional[str] = None,
    max_pages: int = 200,
    cache_path: Optional[str] = None,
    datadome_cooldown: int = 60,
    captcha_timeout: int = 300,
    search_vocabulary: Optional[Set[str]] = None,
) -> List[Tuple[int, str]]:
    """Crawl the Pond5 contributor portfolio and return all (asset_id, cdn_url) pairs.

    Strategy (two phases):

    Phase 1 — Incremental update (sb=6, newest first): navigates from the newest page and
    stops as soon as ``_MAX_CONSECUTIVE_ZERO_PAGES`` consecutive pages yield no new assets —
    meaning everything older is already in the cache.  On the very first run (empty cache) this
    traverses the full ~43 pages; on subsequent runs it typically needs only 2–5 pages.

    Phase 2 — Letter-prefix search: recursively searches ``search=a``, ``search=b``, ...,
    ``search=z`` to reach assets not exposed by any sort order.  When Pond5 reports
    ``expected_total > _PREFIX_LIMIT`` (2 048) the prefix is subdivided (``ab``, ``ac``, …)
    up to ``_PREFIX_MAX_DEPTH`` levels deep.  This guarantees coverage regardless of
    portfolio size.

    The result is persisted to *cache_path* (CSV) after each run so subsequent calls start
    with all previously discovered assets pre-loaded (cumulative, never removes entries).

    DataDome recovery: when a block is detected the crawler waits *datadome_cooldown* seconds
    then opens a visible browser for manual CAPTCHA solving (up to *captcha_timeout* seconds).

    :param portfolio_url: Full portfolio URL from public_portfolios.json.
    :param headless: Run browser headless when True.
    :param profile_dir: Path to the persistent Chromium profile directory.
    :param max_pages: Safety limit on pages per sort/keyword pass.
    :param cache_path: Path to the CSV portfolio cache file.  Loaded at start and saved after
        each successful crawl.  Pass ``None`` to disable caching (stateless run).
    :param datadome_cooldown: Seconds to wait after a DataDome block before recovery.
    :param captcha_timeout: Seconds to wait in the visible browser for CAPTCHA solving.
    :param search_vocabulary: Pre-computed set of substrings from photo metadata words
        (built via ``build_search_vocabulary``).  Phase 2 only searches letter combinations
        present in this set — e.g. "aaa" is skipped if no photo word contains "aaa".
        Pass ``None`` to search all letter combinations unconditionally.
    :return: List of (asset_id, cdn_preview_url) tuples for every portfolio asset found.
    """
    from playwright.sync_api import sync_playwright

    contributor_name = extract_contributor_name(portfolio_url)
    logging.info("Crawling Pond5 portfolio: %s (contributor: %s)", portfolio_url, contributor_name)

    if not profile_dir or not os.path.isdir(profile_dir):
        logging.warning(
            "No persistent profile at %s — DataDome will likely block. "
            "Run: python save_bank_session.py --bank Pond5",
            profile_dir,
        )

    # Load cache → initialise seen_ids/assets from previously discovered assets
    cache = PortfolioCache(cache_path) if cache_path else None
    cached = cache.load() if cache else []
    seen_ids: Set[int] = {asset_id for asset_id, _ in cached}
    assets: List[Tuple[int, str]] = list(cached)
    logging.info("Cache: %d assets pre-loaded", len(assets))
    expected_total: Optional[int] = None

    with sync_playwright() as pw:
        ctx = _open_browser_context(pw, profile_dir, headless)
        browser_page = ctx.new_page()
        state = [ctx, browser_page]  # shared mutable state for the entire crawl
        try:
            # Phase 1: incremental update — sb=6 (newest first), stops when all pages cached
            logging.info("=== Phase 1: incremental update (sb=6) | cached: %d ===", len(assets))
            for attempt in range(_RECOVERY_MAX_RETRIES + 1):
                ctx, browser_page = state
                new_count, total, datadome_hit = _crawl_sort_pass(
                    browser_page, portfolio_url, "6", seen_ids, assets, max_pages
                )
                if not datadome_hit:
                    break
                if attempt < _RECOVERY_MAX_RETRIES:
                    ctx.close()
                    recovered = _recover_from_datadome(
                        pw, portfolio_url, profile_dir, datadome_cooldown, captcha_timeout
                    )
                    ctx = _open_browser_context(pw, profile_dir, headless)
                    browser_page = ctx.new_page()
                    state[0], state[1] = ctx, browser_page
                    if not recovered:
                        logging.warning("Phase 1: recovery failed — continuing with partial results")
                        break
                else:
                    logging.warning("Phase 1: still blocked after recovery — continuing")

            if total is not None:
                expected_total = total
            logging.info(
                "Phase 1 done: +%d new assets (unique total: %d / %s)",
                new_count, len(assets), expected_total or "?",
            )

            # Phase 2: letter-prefix search — reuses the same browser context as Phase 1
            if expected_total is None or len(assets) < expected_total:
                logging.info(
                    "=== Phase 2: letter-prefix search | unique so far: %d / %s ===",
                    len(assets), expected_total or "?",
                )
                _crawl_letter_prefix_phase(
                    pw, portfolio_url, profile_dir, headless,
                    seen_ids, assets, max_pages,
                    datadome_cooldown, captcha_timeout,
                    search_vocabulary=search_vocabulary,
                    cache=cache,
                    _state=state,
                )
                logging.info(
                    "Phase 2 done: unique total: %d / %s",
                    len(assets), expected_total or "?",
                )
            else:
                logging.info("Phase 2 skipped — all %d expected assets already found", expected_total)

        finally:
            ctx, browser_page = state
            try:
                ctx.close()
            except Exception:
                pass

    # Persist updated cache
    if cache:
        cache.save(assets)

    logging.info(
        "Pond5 portfolio crawl complete: %d assets found (expected: %s)",
        len(assets),
        expected_total or "?",
    )
    return assets


class Pond5Adapter(BankDiscoveryAdapter):
    """Discover Pond5 candidates via portfolio crawl + CDN preview URLs.

    Requires a pre-built portfolio index passed as ``portfolio_index`` kwarg.
    Contributor name is derived from the portfolio URL, not passed separately.
    """

    @property
    def bank_name(self) -> str:
        """Return canonical bank name."""
        return "Pond5"

    def discover(self, record: PhotoRecord, **kwargs) -> List[Candidate]:
        """Return Candidate objects for all assets in the portfolio index.

        :param record: PhotoRecord to search for (used only for logging).
        :param kwargs:
            - ``portfolio_index`` (List[Tuple[int, str]]): list of
              (asset_id, cdn_preview_url) from :func:`crawl_pond5_portfolio`.
            - ``contributor_name`` (str): contributor username for identity matching.
        :return: List of Candidates (one per portfolio asset), or empty list
            when no index is provided.
        """
        portfolio_index: Optional[List[Tuple[int, str]]] = kwargs.get("portfolio_index")
        contributor_name: str = kwargs.get("contributor_name", "")

        if not portfolio_index:
            logging.debug("Pond5Adapter.discover: no portfolio_index for %s", record.file)
            return []

        candidates: List[Candidate] = []
        for asset_id, cdn_url in portfolio_index:
            candidates.append(
                Candidate(
                    bank=self.bank_name,
                    url=f"https://www.pond5.com/stock-footage/{asset_id}/",
                    preview_url=cdn_url,
                    contributor_name=contributor_name,
                    asset_id=str(asset_id),
                )
            )
        return candidates