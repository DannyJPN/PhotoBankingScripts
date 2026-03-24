"""Runner for public portfolio approval detection."""

from __future__ import annotations

import logging
import re
from html import unescape
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

from markphotomediaapprovalstatuslib.constants import STATUS_APPROVED, STATUS_CHECKED, STATUS_COLUMN_KEYWORD
from markphotomediaapprovalstatuslib.public_portfolio.browser import browser_context
from markphotomediaapprovalstatuslib.public_portfolio.config_store import load_effective_config
from markphotomediaapprovalstatuslib.public_portfolio.constants import (
    DEFAULT_PUBLIC_PORTFOLIO_CONFIG,
    PUBLIC_PORTFOLIO_INITIAL_WAIT_MS,
    PUBLIC_PORTFOLIO_MAX_PAGES,
    PUBLIC_PORTFOLIO_MAX_SCROLLS,
    PUBLIC_PORTFOLIO_MAX_STALE_PAGES,
    PUBLIC_PORTFOLIO_PAGE_TIMEOUT_MS,
    PUBLIC_PORTFOLIO_SCROLL_WAIT_MS,
    PUBLIC_PORTFOLIO_STABLE_SCROLLS,
)
from markphotomediaapprovalstatuslib.public_portfolio.diagnostics import (
    collect_page_diagnostics,
    detect_blocked_page,
    log_page_diagnostics,
)
from markphotomediaapprovalstatuslib.public_portfolio.matching import match_record_to_public_assets
from markphotomediaapprovalstatuslib.public_portfolio.models import PublicAsset
from markphotomediaapprovalstatuslib.public_portfolio.banks import BANK_ADAPTERS
from markphotomediaapprovalstatuslib.public_portfolio.constants import BLOCKED_BANKS
from markphotomediaapprovalstatuslib.public_portfolio.session import run_session_saver
from markphotomediaapprovalstatuslib.status_handler import filter_records_by_bank_status
from shared.file_operations import save_csv_with_backup


def _fetch_html(context, url: str, wait_ms: int = 10000, timeout_ms: int = 120000) -> str:
    """Fetch rendered page HTML using Playwright.

    :param context: Playwright browser context.
    :param url: URL to fetch.
    :param wait_ms: Milliseconds to wait after page load for JS rendering.
    :param timeout_ms: Page load timeout in milliseconds.
    :return: Rendered HTML content.
    """
    page = context.new_page()
    try:
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.wait_for_timeout(wait_ms)
        return page.content()
    except Exception as exc:
        logging.warning("Failed to fetch %s: %s", url, exc)
        return ""
    finally:
        page.close()


def _fetch_html_with_scroll(
    context,
    url: str,
    item_url_regex: Optional[str] = None,
    max_scrolls: int = PUBLIC_PORTFOLIO_MAX_SCROLLS,
    scroll_wait_ms: int = PUBLIC_PORTFOLIO_SCROLL_WAIT_MS,
    initial_wait_ms: int = PUBLIC_PORTFOLIO_INITIAL_WAIT_MS,
    timeout_ms: int = PUBLIC_PORTFOLIO_PAGE_TIMEOUT_MS,
    stable_scrolls: int = PUBLIC_PORTFOLIO_STABLE_SCROLLS,
) -> Tuple[str, Dict[str, object]]:
    """Fetch page HTML with infinite scroll to load all content.

    :param context: Playwright browser context.
    :param url: URL to fetch.
    :param max_scrolls: Maximum number of scroll attempts.
    :param scroll_wait_ms: Milliseconds to wait after each scroll.
    :param initial_wait_ms: Milliseconds to wait after initial page load.
    :param timeout_ms: Page load timeout in milliseconds.
    :param stable_scrolls: Number of consecutive no-growth checks before stopping.
    :param item_url_regex: Optional bank-specific asset URL regex.
    :return: Tuple of rendered HTML content and page diagnostics.
    """
    page = context.new_page()
    try:
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="load", timeout=timeout_ms)
        page.wait_for_timeout(initial_wait_ms)

        prev_growth_marker = 0
        unchanged_scrolls = 0
        for scroll_index in range(1, max_scrolls + 1):
            scroll_state = page.evaluate(
                """
() => {
  const textPatterns = [
    "load more",
    "show more",
    "see more",
    "more results",
    "zobrazit více",
    "načíst další",
    "načíst více"
  ];

  const isVisible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };

  const getDescriptor = (el) => {
    if (!el) {
      return "document";
    }
    const cls = (el.className || "").toString().trim().replace(/\\s+/g, ".").slice(0, 80);
    return `${el.tagName.toLowerCase()}#${el.id || ""}${cls ? "." + cls : ""}`;
  };

  const candidates = [];
  const pushCandidate = (el, kind) => {
    if (!el) {
      return;
    }
    if (typeof el.getBoundingClientRect !== "function") {
      return;
    }
    let rect;
    let style;
    try {
      rect = el.getBoundingClientRect();
      style = getComputedStyle(el);
    } catch (error) {
      return;
    }
    if (!rect || !style) {
      return;
    }
    const scrollHeight = el.scrollHeight || 0;
    const clientHeight = el.clientHeight || 0;
    const scrollableDelta = scrollHeight - clientHeight;
    const overflowY = style.overflowY;
    const visible = rect.width > 0 && rect.height > 0;
    if (kind !== "document" && (!visible || scrollableDelta < 150)) {
      return;
    }
    const score =
      (kind === "document" ? 1_000_000 : 0) +
      Math.max(scrollableDelta, 0) +
      Math.max(rect.height, 0) * 2 +
      (["auto", "scroll"].includes(overflowY) ? 50_000 : 0);
    candidates.push({
      el,
      kind,
      score,
      descriptor: getDescriptor(el),
      scrollHeight,
      clientHeight,
      scrollTop: el.scrollTop || 0,
      overflowY,
    });
  };

  pushCandidate(document.scrollingElement || document.documentElement || document.body, "document");
  for (const el of document.querySelectorAll("*")) {
    pushCandidate(el, "element");
  }

  candidates.sort((a, b) => b.score - a.score);
  const target = candidates[0] || {
    el: document.scrollingElement || document.documentElement || document.body,
    kind: "document",
    descriptor: "document",
    scrollHeight: document.documentElement.scrollHeight,
    clientHeight: window.innerHeight,
    scrollTop: window.scrollY,
    overflowY: "visible",
  };

  if (target.kind === "document") {
    window.scrollTo(0, Math.max(document.body.scrollHeight, document.documentElement.scrollHeight));
  } else {
    target.el.scrollTo(0, target.el.scrollHeight);
  }

  let clickedLoadMore = false;
  let clickedText = "";
  const clickable = [...document.querySelectorAll("button, a, [role='button']")];
  for (const el of clickable) {
    if (!isVisible(el) || el.hasAttribute("disabled") || el.getAttribute("aria-disabled") === "true") {
      continue;
    }
    const text = (el.innerText || el.getAttribute("aria-label") || "").trim().toLowerCase();
    const href = (el.getAttribute("href") || "").trim().toLowerCase();
    if (!text) {
      continue;
    }
    const normalizedText = text.replace(/\\s+/g, " ");
    const isLoadMoreText = textPatterns.some((pattern) => normalizedText === pattern || normalizedText.startsWith(pattern + " "));
    const isSafeClickTarget =
      el.tagName === "BUTTON" ||
      !href ||
      href === "#" ||
      href.startsWith("javascript:");
    if (isLoadMoreText && isSafeClickTarget) {
      el.click();
      clickedLoadMore = true;
      clickedText = text.slice(0, 120);
      break;
    }
  }

  return {
    targetKind: target.kind,
    targetDescriptor: target.descriptor,
    targetScrollTop: target.el ? (target.el.scrollTop || 0) : window.scrollY,
    targetClientHeight: target.el ? (target.el.clientHeight || 0) : window.innerHeight,
    targetScrollHeight: target.el ? (target.el.scrollHeight || 0) : Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
    documentScrollHeight: Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
    clickedLoadMore,
    clickedText,
  };
}
"""
            )
            page.wait_for_timeout(scroll_wait_ms)
            post_scroll_state = page.evaluate(
                """
() => ({
  bodyScrollHeight: document.body.scrollHeight,
  docScrollHeight: document.documentElement.scrollHeight,
  viewportY: window.scrollY,
})
"""
            )
            new_growth_marker = max(
                scroll_state["targetScrollHeight"],
                post_scroll_state["bodyScrollHeight"],
                post_scroll_state["docScrollHeight"],
            )
            logging.debug(
                "Scroll %s for %s: target=%s kind=%s top=%s client=%s targetHeight=%s docHeight=%s viewportY=%s unchanged=%s/%s clickedLoadMore=%s text=%s",
                scroll_index,
                url,
                scroll_state["targetDescriptor"],
                scroll_state["targetKind"],
                scroll_state["targetScrollTop"],
                scroll_state["targetClientHeight"],
                scroll_state["targetScrollHeight"],
                post_scroll_state["docScrollHeight"],
                post_scroll_state["viewportY"],
                unchanged_scrolls,
                stable_scrolls,
                scroll_state["clickedLoadMore"],
                scroll_state["clickedText"],
            )
            if new_growth_marker <= prev_growth_marker:
                unchanged_scrolls += 1
                if unchanged_scrolls >= stable_scrolls:
                    logging.debug(
                        "Stopping scroll for %s after %s consecutive unchanged growth markers at scroll %s.",
                        url,
                        stable_scrolls,
                        scroll_index,
                    )
                    break
            else:
                unchanged_scrolls = 0
            prev_growth_marker = new_growth_marker

        html = page.content()
        diagnostics = collect_page_diagnostics(page, html, item_url_regex=item_url_regex, requested_url=url)
        return html, diagnostics
    except Exception as exc:
        logging.warning("Failed to fetch with scroll %s: %s", url, exc)
        return "", {
            "final_url": url,
            "title": "",
            "body_length": 0,
            "html_length": 0,
            "text_excerpt": "",
            "headings": [],
            "buttons": [],
            "top_nodes": [],
            "top_node_count": 0,
            "regex_match_count": 0,
        }
    finally:
        page.close()


def fetch_public_portfolio_page(
    context,
    url: str,
    item_url_regex: Optional[str] = None,
    max_scrolls: int = PUBLIC_PORTFOLIO_MAX_SCROLLS,
    scroll_wait_ms: int = PUBLIC_PORTFOLIO_SCROLL_WAIT_MS,
    initial_wait_ms: int = PUBLIC_PORTFOLIO_INITIAL_WAIT_MS,
    timeout_ms: int = PUBLIC_PORTFOLIO_PAGE_TIMEOUT_MS,
    stable_scrolls: int = PUBLIC_PORTFOLIO_STABLE_SCROLLS,
) -> Tuple[str, Dict[str, object]]:
    """Public wrapper for fetching and diagnosing a portfolio page."""
    return _fetch_html_with_scroll(
        context,
        url,
        item_url_regex=item_url_regex,
        max_scrolls=max_scrolls,
        scroll_wait_ms=scroll_wait_ms,
        initial_wait_ms=initial_wait_ms,
        timeout_ms=timeout_ms,
        stable_scrolls=stable_scrolls,
    )


def _extract_pagination_marker(url: str) -> Tuple[Optional[str], Optional[int]]:
    """Extract a pagination marker from a URL."""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ("page", "pp", "p", "pg", "pn", "current_page", "offset"):
        values = query.get(key)
        if values:
            try:
                return key, int(values[0])
            except (TypeError, ValueError):
                return key, None

    path_match = re.search(r"/(\d+)\.html?$", parsed.path)
    if path_match:
        try:
            return "path_page", int(path_match.group(1))
        except ValueError:
            return "path_page", None

    return None, None


def _is_related_pagination_link(current_url: str, candidate_url: str) -> bool:
    """Check whether a pagination candidate belongs to the same portfolio listing."""
    current = urlparse(current_url)
    candidate = urlparse(candidate_url)
    if current.netloc.lower() != candidate.netloc.lower():
        return False

    current_path = current.path.rstrip("/")
    candidate_path = candidate.path.rstrip("/")
    if current_path == candidate_path:
        return True

    current_segments = [segment for segment in current_path.split("/") if segment]
    candidate_segments = [segment for segment in candidate_path.split("/") if segment]
    if not current_segments or not candidate_segments:
        return False

    shared_prefix = 0
    for left, right in zip(current_segments, candidate_segments):
        if left == right:
            shared_prefix += 1
        else:
            break

    if shared_prefix >= max(1, min(len(current_segments), len(candidate_segments)) - 1):
        return True

    return current_segments[-1] == candidate_segments[-1]


def _find_next_page(html: str, current_url: str) -> Optional[str]:
    """Find the next relevant pagination URL for the current portfolio page."""
    match = re.search(r"<link[^>]+rel=[\"']next[\"'][^>]+href=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
    if match:
        return urljoin(current_url, unescape(match.group(1)))
    match = re.search(r"<a[^>]+rel=[\"']next[\"'][^>]+href=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
    if match:
        return urljoin(current_url, unescape(match.group(1)))

    current_key, current_value = _extract_pagination_marker(current_url)
    if current_key is None:
        current_key = "page"
        current_value = 1
    elif current_value is None:
        current_value = 0 if current_key == "offset" else 1

    href_matches = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html, re.IGNORECASE)
    candidates: List[Tuple[int, str]] = []
    seen = set()
    for raw_href in href_matches:
        href = urljoin(current_url, unescape(raw_href))
        if href in seen or not _is_related_pagination_link(current_url, href):
            continue
        seen.add(href)
        key, value = _extract_pagination_marker(href)
        if key is None or value is None or key != current_key or value <= current_value:
            continue
        candidates.append((value, href))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _asset_identity(asset: PublicAsset) -> Tuple[str, str]:
    """Create a stable identity for deduplicating portfolio assets across pages."""
    return (asset.url.strip().lower(), asset.title.strip().lower())


def _contributor_from_url(portfolio_url: str) -> str:
    """Derive a contributor identifier from the portfolio URL.

    :param portfolio_url: Portfolio page URL.
    :return: Contributor identifier string.
    """
    from urllib.parse import urlparse

    path = urlparse(portfolio_url).path.rstrip("/")
    last_segment = path.split("/")[-1] if "/" in path else path
    last_segment = re.sub(r"[_-]info$", "", last_segment)
    last_segment = re.sub(r"^profile[_-]?", "", last_segment)
    last_segment = re.sub(r"^portfolio[_-]?", "", last_segment)
    return last_segment or "owner"


def _crawl_portfolio(adapter, context, portfolio_url: str, contributor_id: str) -> Tuple[List[PublicAsset], bool]:
    """Crawl portfolio with infinite scroll to load all content.

    Uses scrolling to trigger lazy-loading of additional photos.
    Does NOT visit individual detail pages (they are often blocked by anti-bot).

    :param adapter: Bank adapter instance.
    :param context: Playwright browser context.
    :param portfolio_url: Portfolio page URL.
    :param contributor_id: Known contributor identifier.
    :return: Tuple of (assets, blocked_by_anti_bot).
    """
    all_assets: List[PublicAsset] = []
    seen_assets = set()
    visited_urls = set()
    stale_pages = 0
    current_url = portfolio_url

    for page_index in range(1, PUBLIC_PORTFOLIO_MAX_PAGES + 1):
        if current_url in visited_urls:
            logging.warning("%s: already visited portfolio page %s, stopping pagination loop.", adapter.bank, current_url)
            break
        visited_urls.add(current_url)

        logging.info("%s portfolio crawl page %s: %s", adapter.bank, page_index, current_url)
        html, diagnostics = fetch_public_portfolio_page(
            context,
            current_url,
            item_url_regex=adapter.item_url_regex,
            max_scrolls=PUBLIC_PORTFOLIO_MAX_SCROLLS,
            scroll_wait_ms=PUBLIC_PORTFOLIO_SCROLL_WAIT_MS,
            initial_wait_ms=PUBLIC_PORTFOLIO_INITIAL_WAIT_MS,
            timeout_ms=PUBLIC_PORTFOLIO_PAGE_TIMEOUT_MS,
            stable_scrolls=PUBLIC_PORTFOLIO_STABLE_SCROLLS,
        )
        blocked, reason = detect_blocked_page(diagnostics)
        if blocked:
            log_page_diagnostics(adapter.bank, diagnostics, reason=reason, blocked=True)
            return [], True

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            log_page_diagnostics(adapter.bank, diagnostics)

        page_assets = adapter.extract_assets_from_portfolio(html, contributor_id)
        new_assets = 0
        for asset in page_assets:
            identity = _asset_identity(asset)
            if identity in seen_assets:
                continue
            seen_assets.add(identity)
            all_assets.append(asset)
            new_assets += 1

        logging.info(
            "%s: page %s extracted=%s new=%s cumulative=%s",
            adapter.bank,
            page_index,
            len(page_assets),
            new_assets,
            len(all_assets),
        )

        if new_assets == 0:
            stale_pages += 1
            if stale_pages >= PUBLIC_PORTFOLIO_MAX_STALE_PAGES:
                logging.info(
                    "%s: stopping after %s consecutive pages without new assets.",
                    adapter.bank,
                    stale_pages,
                )
                break
        else:
            stale_pages = 0

        next_page_url = _find_next_page(html, current_url)
        if not next_page_url:
            break
        current_url = next_page_url

    logging.info("%s: extracted %d assets across %d page(s)", adapter.bank, len(all_assets), len(visited_urls))
    return all_assets, False


def _crawl_bank_portfolio(
    adapter_cls,
    bank: str,
    headless: bool,
    portfolio_url: str,
    contributor_id: str,
) -> Tuple[List[PublicAsset], bool]:
    """Open a short-lived browser context, crawl one bank portfolio, and close it."""
    with browser_context(headless=headless, bank=bank) as context:
        adapter = adapter_cls(context)
        return _crawl_portfolio(adapter, context, portfolio_url, contributor_id)


def process_public_portfolio_approval(
    all_data: List[dict],
    filtered_data: List[dict],
    csv_path: str,
    config_path: Optional[str] = None,
    headless: bool = True,
    discover_only: bool = False,
) -> bool:
    """Process public portfolio approval detection for all supported banks.

    Creates separate browser contexts per bank to support bank-specific cookies.
    """
    config_path = config_path or DEFAULT_PUBLIC_PORTFOLIO_CONFIG
    config = load_effective_config(config_path)
    config.setdefault("banks", {})
    changes_made = False
    summary = {
        "banks_scanned": 0,
        "approved_matches": 0,
        "ambiguous": 0,
        "blocked": 0,
    }

    for bank, adapter_cls in BANK_ADAPTERS.items():
        adapter = adapter_cls(None)
        if not adapter.is_supported():
            logging.info("%s: public portfolio mode not supported, skipping", bank)
            continue

        bank_records = filter_records_by_bank_status(filtered_data, bank, STATUS_CHECKED)
        if not bank_records:
            logging.debug("%s: no records with checked status, skipping", bank)
            continue

        bank_config = config["banks"].get(bank, {})
        portfolio_url = bank_config.get("portfolio_url")

        if not portfolio_url:
            logging.warning("%s: no portfolio URL configured, skipping.", bank)
            continue

        summary["banks_scanned"] += 1
        bank_changes = False

        contributor_id = bank_config.get("contributor_id") or _contributor_from_url(portfolio_url)
        assets, blocked = _crawl_bank_portfolio(
            adapter_cls,
            bank,
            headless,
            portfolio_url,
            contributor_id,
        )

        if blocked and bank in BLOCKED_BANKS:
            logging.info(
                "%s: triggering interactive session refresh to solve CAPTCHA and save cookies.",
                bank,
            )
            if run_session_saver(bank):
                assets, blocked = _crawl_bank_portfolio(
                    adapter_cls,
                    bank,
                    headless,
                    portfolio_url,
                    contributor_id,
                )
            else:
                logging.warning("%s: session refresh failed or was cancelled.", bank)

        if not assets:
            logging.warning(
                "%s: no assets found (empty portfolio, extractor mismatch, or still blocked). Run 'python save_bank_session.py --bank %s' to save cookies if this bank is protected.",
                bank,
                bank,
            )
            if blocked:
                summary["blocked"] += 1
            continue

        logging.info("%s: %d total assets from portfolio", bank, len(assets))

        if discover_only:
            continue

        for record in bank_records:
            title = record.get("Název", "")
            description = record.get("Popis", "")
            match = match_record_to_public_assets(bank, contributor_id, title, description, assets)

            if match.approved:
                status_column = f"{bank} {STATUS_COLUMN_KEYWORD}"
                if status_column in record and record[status_column] != STATUS_APPROVED:
                    record[status_column] = STATUS_APPROVED
                    changes_made = True
                    bank_changes = True
                    summary["approved_matches"] += 1
            elif match.matched_by == "AMBIGUOUS":
                summary["ambiguous"] += 1

        if bank_changes:
            save_csv_with_backup(all_data, csv_path)

    logging.info(
        "Public portfolio summary: banks=%s approved=%s ambiguous=%s blocked=%s",
        summary["banks_scanned"],
        summary["approved_matches"],
        summary["ambiguous"],
        summary["blocked"],
    )
    return changes_made
