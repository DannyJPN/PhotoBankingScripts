"""Unit tests for models.py."""

from markphotomediaapprovalstatuslib.models import Candidate, DetectionResult, Evidence, PhotoRecord


def test_photo_record__instantiation():
    r = PhotoRecord(
        file="DSC00001.JPG",
        path="/photos",
        title="Flower",
        description="A flower",
        keywords="flower, nature",
        bank_statuses={"ShutterStock": "kontrolováno"},
        local_file_path="/photos/DSC00001.JPG",
    )
    assert r.file == "DSC00001.JPG"
    assert r.bank_statuses["ShutterStock"] == "kontrolováno"


def test_candidate__defaults():
    c = Candidate(bank="Pond5", url="http://x", preview_url="http://x/p.jpg", contributor_name="alice")
    assert c.asset_id is None
    assert c.title == ""


def test_evidence__defaults():
    c = Candidate(bank="Pond5", url="http://x", preview_url="http://x/p.jpg", contributor_name="alice")
    ev = Evidence(candidate=c)
    assert ev.phash_distance is None
    assert ev.dhash_distance is None
    assert ev.contributor_match is False
    assert ev.dimension_match is None


def test_detection_result__defaults():
    r = DetectionResult(record_file="DSC00001.JPG", bank="Pond5", outcome="NOT_FOUND")
    assert r.matched_url is None
    assert r.matched_id is None
    assert r.evidence is None
    assert r.reason == ""
    assert r.timestamp == ""
