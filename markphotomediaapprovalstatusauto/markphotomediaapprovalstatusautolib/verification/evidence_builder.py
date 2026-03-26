"""Builds an Evidence object by comparing a local file against a Candidate."""

import logging
from typing import Optional

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
