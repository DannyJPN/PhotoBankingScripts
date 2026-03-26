"""Diagnostics helpers for public portfolio crawling."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

CHALLENGE_MARKERS = (
    "captcha",
    "verify you are human",
    "verify you are a human",
    "security check",
    "attention required",
    "just a moment",
    "checking if the site connection is secure",
    "enable javascript",
    "access denied",
    "unusual traffic",
    "datadome",
    "cloudflare",
    "bot verification",
    "challenge",
)


def collect_page_diagnostics(
    page,
    html: str,
    item_url_regex: Optional[str] = None,
    requested_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Collect a lightweight page snapshot for troubleshooting."""
    snapshot = page.evaluate(
        """
() => {
  const body = document.body;
  const normalize = (value) => (value || "").replace(/\\s+/g, " ").trim();
  const topNodes = Array.from(body ? body.children : []).slice(0, 8).map((el) => {
    const cls = (el.className || "").toString().trim().replace(/\\s+/g, ".").slice(0, 60);
    return `${el.tagName.toLowerCase()}#${el.id || ""}${cls ? "." + cls : ""}`;
  });
  const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
    .map((el) => normalize(el.innerText))
    .filter(Boolean)
    .slice(0, 6);
  const buttons = Array.from(document.querySelectorAll("button, a, [role='button']"))
    .map((el) => normalize(el.innerText || el.getAttribute("aria-label")))
    .filter(Boolean)
    .slice(0, 12);
  const bodyText = normalize(body ? body.innerText : "");
  return {
    finalUrl: window.location.href,
    title: document.title || "",
    bodyLength: body && body.innerHTML ? body.innerHTML.length : 0,
    textExcerpt: bodyText.slice(0, 500),
    headings,
    buttons,
    topNodes,
    topNodeCount: body ? body.children.length : 0,
  };
}
"""
    )

    regex_match_count = 0
    if item_url_regex and html:
        try:
            regex_match_count = len({match.group(0) for match in re.finditer(item_url_regex, html, re.IGNORECASE)})
        except re.error as exc:
            logging.debug("Failed to count item regex matches: %s", exc)

    return {
        "requested_url": requested_url or "",
        "final_url": snapshot.get("finalUrl", ""),
        "title": snapshot.get("title", ""),
        "body_length": snapshot.get("bodyLength", 0),
        "html_length": len(html),
        "text_excerpt": snapshot.get("textExcerpt", ""),
        "headings": snapshot.get("headings", []),
        "buttons": snapshot.get("buttons", []),
        "top_nodes": snapshot.get("topNodes", []),
        "top_node_count": snapshot.get("topNodeCount", 0),
        "regex_match_count": regex_match_count,
    }


def detect_blocked_page(diagnostics: Dict[str, Any]) -> Tuple[bool, str]:
    """Detect likely challenge or placeholder pages."""
    combined_text = " ".join(
        filter(
            None,
            [
                diagnostics.get("title", ""),
                diagnostics.get("final_url", ""),
                diagnostics.get("text_excerpt", ""),
                " ".join(diagnostics.get("headings", [])),
                " ".join(diagnostics.get("buttons", [])),
            ],
        )
    ).lower()

    for marker in CHALLENGE_MARKERS:
        if marker in combined_text:
            return True, f"challenge-marker:{marker}"

    html_length = diagnostics.get("html_length", 0)
    body_length = diagnostics.get("body_length", 0)
    regex_match_count = diagnostics.get("regex_match_count", 0)
    top_node_count = diagnostics.get("top_node_count", 0)
    final_url = diagnostics.get("final_url", "")
    requested_url = diagnostics.get("requested_url", "")
    title = diagnostics.get("title", "").strip().lower()
    requested_host = urlparse(requested_url).netloc.lower().removeprefix("www.")
    host = urlparse(final_url).netloc.lower().removeprefix("www.")

    if requested_host and host and requested_host != host:
        return True, f"unexpected-redirect:{requested_host}->{host}"

    if html_length < 2500 and body_length < 2000 and regex_match_count == 0:
        return True, "minimal-shell"

    if host and title in {host, f"{host}/"} and regex_match_count == 0 and html_length < 8000:
        return True, "generic-domain-title"

    if top_node_count <= 2 and html_length < 4000 and regex_match_count == 0:
        return True, "sparse-dom-shell"

    return False, ""


def log_page_diagnostics(bank: str, diagnostics: Dict[str, Any], reason: str = "", blocked: bool = False) -> None:
    """Log diagnostics in a compact, human-readable form."""
    log_fn = logging.warning if blocked else logging.info
    log_fn(
        "%s diagnostics: final_url=%s title=%s html=%s body=%s regex_matches=%s top_nodes=%s reason=%s",
        bank,
        diagnostics.get("final_url", ""),
        diagnostics.get("title", ""),
        diagnostics.get("html_length", 0),
        diagnostics.get("body_length", 0),
        diagnostics.get("regex_match_count", 0),
        diagnostics.get("top_node_count", 0),
        reason or "-",
    )

    headings = diagnostics.get("headings", [])
    if headings:
        log_fn("%s diagnostics headings: %s", bank, " | ".join(headings[:4]))

    buttons = diagnostics.get("buttons", [])
    if buttons:
        log_fn("%s diagnostics buttons: %s", bank, " | ".join(buttons[:6]))

    top_nodes = diagnostics.get("top_nodes", [])
    if top_nodes:
        log_fn("%s diagnostics top_nodes: %s", bank, " | ".join(top_nodes[:6]))

    text_excerpt = diagnostics.get("text_excerpt", "")
    if text_excerpt:
        clean_excerpt = re.sub(r"[\u200b\u200c\u200d\ufeff]", " ", text_excerpt)
        clean_excerpt = re.sub(r"\s+", " ", clean_excerpt).strip()
        log_fn("%s diagnostics excerpt: %s", bank, clean_excerpt[:300])
