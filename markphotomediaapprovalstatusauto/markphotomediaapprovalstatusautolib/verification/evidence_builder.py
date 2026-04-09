"""Builds an Evidence object by comparing a local file against a Candidate."""

import logging
from typing import Dict, Iterable, List, Optional, Tuple

import imagehash

from markphotomediaapprovalstatusautolib.models import Candidate, Evidence
from markphotomediaapprovalstatusautolib.transport.http_client import HttpClient
from markphotomediaapprovalstatusautolib.verification.hash_cache import HashCache
from markphotomediaapprovalstatusautolib.verification.image_hasher import (
    generate_dhash,
    generate_phash,
    hamming_distance,
)
from markphotomediaapprovalstatusautolib.verification.preview_downloader import download_preview


def build_evidence(
    local_file_path: str,
    contributor_name: str,
    candidate: Candidate,
    http_client: HttpClient,
    hash_cache: HashCache,
    preview_cache_dir: str,
) -> Evidence:
    """Compute verification evidence for one local file against one Candidate.

    :param local_file_path: Absolute path to the local photo file.
    :param contributor_name: Expected contributor name for identity matching.
    :param candidate: Discovered Candidate from a bank adapter.
    :param http_client: Shared HttpClient for downloading previews.
    :param hash_cache: HashCache for local file hashes.
    :param preview_cache_dir: Directory for caching downloaded preview images.
    :return: Evidence object with all collected signals.
    """
    contributor_match = bool(
        candidate.contributor_name
        and candidate.contributor_name.lower().strip() == contributor_name.lower().strip()
    )

    local_hashes = hash_cache.get_or_compute(local_file_path)
    if local_hashes is None or not candidate.preview_url:
        return Evidence(
            candidate=candidate,
            contributor_match=contributor_match,
        )

    local_phash, local_dhash = local_hashes
    preview_bytes = download_preview(candidate.preview_url, http_client, preview_cache_dir)
    if preview_bytes is None:
        return Evidence(
            candidate=candidate,
            contributor_match=contributor_match,
        )

    try:
        remote_phash = generate_phash(preview_bytes)
        remote_dhash = generate_dhash(preview_bytes)
        phash_dist = hamming_distance(local_phash, remote_phash)
        dhash_dist = hamming_distance(local_dhash, remote_dhash)
    except Exception as exc:
        logging.warning("Hash comparison failed for preview %s: %s", candidate.preview_url, exc)
        return Evidence(
            candidate=candidate,
            contributor_match=contributor_match,
        )

    return Evidence(
        candidate=candidate,
        phash_distance=phash_dist,
        dhash_distance=dhash_dist,
        contributor_match=contributor_match,
    )


def build_portfolio_phash_index(
    portfolio: Iterable[Tuple[int, str]],
    http_client: HttpClient,
    preview_cache_dir: str,
) -> Dict[int, Tuple[imagehash.ImageHash, imagehash.ImageHash]]:
    """Download portfolio previews and compute pHash + dHash for each asset.

    Accepts any iterable of (asset_id, cdn_preview_url) pairs so callers can wrap
    the list with a progress-bar iterator (e.g. tqdm) without coupling the library
    to any UI dependency.

    Assets whose preview cannot be downloaded or hashed are skipped with a warning.

    :param portfolio: Iterable of (asset_id, cdn_preview_url) from crawl_pond5_portfolio.
    :param http_client: Shared HttpClient for downloading previews.
    :param preview_cache_dir: Directory for caching downloaded preview images.
    :return: Dict mapping asset_id to (phash, dhash) tuple.
    """
    index: Dict[int, Tuple[imagehash.ImageHash, imagehash.ImageHash]] = {}
    total = 0
    for asset_id, cdn_url in portfolio:
        total += 1
        preview_bytes = download_preview(cdn_url, http_client, preview_cache_dir)
        if preview_bytes is None:
            logging.warning("Could not download preview for asset %d — skipped", asset_id)
            continue
        try:
            index[asset_id] = (generate_phash(preview_bytes), generate_dhash(preview_bytes))
        except Exception as exc:
            logging.warning("Could not hash preview for asset %d: %s — skipped", asset_id, exc)
    logging.info("Portfolio pHash index built: %d / %d assets", len(index), total)
    return index


def find_best_portfolio_match(
    local_phash: imagehash.ImageHash,
    portfolio_index: Dict[int, Tuple[imagehash.ImageHash, imagehash.ImageHash]],
) -> Tuple[Optional[int], int]:
    """Find the portfolio asset with the smallest pHash Hamming distance.

    :param local_phash: pHash of the local file.
    :param portfolio_index: Pre-computed index from :func:`build_portfolio_phash_index`.
    :return: (best_asset_id, best_phash_dist) — asset_id is None when index is empty.
    """
    best_id: Optional[int] = None
    best_dist = 999
    for asset_id, (remote_phash, _) in portfolio_index.items():
        dist = hamming_distance(local_phash, remote_phash)
        if dist < best_dist:
            best_dist = dist
            best_id = asset_id
    return best_id, best_dist


def find_best_combined_match(
    local_phash: imagehash.ImageHash,
    local_dhash: imagehash.ImageHash,
    portfolio_index: Dict[int, Tuple[imagehash.ImageHash, imagehash.ImageHash]],
) -> Tuple[Optional[int], int, int]:
    """Find the portfolio asset with the smallest combined pHash+dHash Hamming distance.

    Used as a fallback when phash-only matching fails (distance exceeds PHASH_THRESHOLD).
    Combined scoring distinguishes image variants (sharpen, BW, negative) that may
    accidentally score lower on pHash alone but are correctly discriminated by dHash.

    :param local_phash: pHash of the local file.
    :param local_dhash: dHash of the local file.
    :param portfolio_index: Pre-computed index from :func:`build_portfolio_phash_index`.
    :return: (best_asset_id, best_phash_dist, best_dhash_dist) — asset_id is None when index is empty.
    """
    best_id: Optional[int] = None
    best_phash_dist = 999
    best_dhash_dist = 999
    best_combined = 999
    for asset_id, (remote_phash, remote_dhash) in portfolio_index.items():
        pd = hamming_distance(local_phash, remote_phash)
        dd = hamming_distance(local_dhash, remote_dhash)
        combined = pd + dd
        if combined < best_combined:
            best_combined = combined
            best_phash_dist = pd
            best_dhash_dist = dd
            best_id = asset_id
    return best_id, best_phash_dist, best_dhash_dist
