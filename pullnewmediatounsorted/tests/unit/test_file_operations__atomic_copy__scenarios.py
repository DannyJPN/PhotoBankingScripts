"""Regression tests for failure-safe copy publication and concurrent destinations."""

import errno
import os
import builtins
import stat
from pathlib import Path
import subprocess
import sys
import time

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT))

from shared import file_operations as operations


@pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EIO])
@pytest.mark.parametrize("concurrent_destination", [False, True])
def test_copy_file__partial_write_never_reaches_final_name(tmp_path, monkeypatch, error_number, concurrent_destination):
    """Keep partial bytes temporary when writing fails, even if another writer arrives."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"complete photograph")

    def fail_copy(source, temporary):
        assert Path(temporary.name).parent == dest.parent
        assert Path(temporary.name).name.startswith(".tmp_copy_")
        temporary.write(b"partial")
        if concurrent_destination:
            dest.write_bytes(b"other complete photograph")
        raise OSError(error_number, "injected write failure")

    monkeypatch.setattr(operations.shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError) as failure:
        operations.copy_file(str(src), str(dest))

    assert failure.value.errno == error_number
    if concurrent_destination:
        assert dest.read_bytes() == b"other complete photograph"
    else:
        assert not dest.exists()
    assert not list(tmp_path.glob(".tmp_copy_*"))
    assert src.read_bytes() == b"complete photograph"


def test_copy_file__failed_flush_prevents_publication(tmp_path, monkeypatch):
    """A failed durability barrier must never expose the final pathname."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"complete")

    def fail_fsync(fd):
        raise OSError(errno.EIO, "injected flush failure")

    monkeypatch.setattr(operations.os, "fsync", fail_fsync)
    with pytest.raises(OSError):
        operations.copy_file(str(src), str(dest))

    assert not dest.exists()
    assert not list(tmp_path.glob(".tmp_copy_*"))


@pytest.mark.parametrize("same_content", [False, True])
@pytest.mark.parametrize("overwrite", [False, True])
def test_copy_file__concurrent_destination_is_never_replaced(tmp_path, monkeypatch, same_content, overwrite):
    """Exercise the real no-replace publication operation, not just its preflight check."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph")
    concurrent_bytes = b"photograph" if same_content else b"other file"
    publish = operations._publish_copy

    def race(temporary, destination):
        dest.write_bytes(concurrent_bytes)
        publish(temporary, destination)

    monkeypatch.setattr(operations, "_publish_copy", race)
    if overwrite and not same_content:
        with pytest.raises(FileExistsError):
            operations.copy_file(str(src), str(dest), overwrite=overwrite)
    else:
        operations.copy_file(str(src), str(dest), overwrite=overwrite)

    assert dest.read_bytes() == concurrent_bytes
    assert not list(tmp_path.glob(".tmp_copy_*"))


def test_copy_file__synced_complete_data_and_metadata_precede_publication(tmp_path, monkeypatch):
    """Check ordering and verify the actual resulting bytes and timestamps."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph" * 1024)
    os.utime(src, (1_600_000_000, 1_600_000_000))
    if sys.platform == "win32":
        operations._set_creation_time_windows(str(src), 1_500_000_000_000_000_000)
    source_stat = src.stat()
    publish = operations._publish_copy
    fsync = operations.os.fsync
    synced = []

    def record_sync(fd):
        fsync(fd)
        synced.append(True)

    def inspect(temporary, destination):
        assert synced
        assert not dest.exists()
        assert operations.compute_file_hash(temporary) == operations.compute_file_hash(str(src))
        assert Path(temporary).stat().st_mtime == source_stat.st_mtime
        if sys.platform == "win32":
            assert Path(temporary).stat().st_ctime == pytest.approx(source_stat.st_ctime, abs=0.001)
        publish(temporary, destination)

    monkeypatch.setattr(operations.os, "fsync", record_sync)
    monkeypatch.setattr(operations, "_publish_copy", inspect)
    operations.copy_file(str(src), str(dest))

    assert operations.compute_file_hash(str(src)) == operations.compute_file_hash(str(dest))
    assert dest.stat().st_mtime == source_stat.st_mtime
    if sys.platform == "win32":
        assert dest.stat().st_ctime == pytest.approx(source_stat.st_ctime, abs=0.001)
    assert not list(tmp_path.glob(".tmp_copy_*"))


def test_copy_file__publish_error_has_no_direct_copy_fallback(tmp_path, monkeypatch):
    """Fail closed when the filesystem cannot perform safe publication."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph")

    def fail_publish(temporary, destination):
        raise OSError(errno.EACCES, "injected publication failure")

    monkeypatch.setattr(operations, "_publish_copy", fail_publish)
    with pytest.raises(OSError):
        operations.copy_file(str(src), str(dest))

    assert not dest.exists()
    assert not list(tmp_path.glob(".tmp_copy_*"))


def test_copy_file__filesystem_without_hard_links_fails_with_actionable_error(tmp_path, monkeypatch):
    """Explain the hard-link requirement instead of a bare OS error, and leave no file behind."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph")

    def no_hard_links(_src, _dest):
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(operations.os, "link", no_hard_links)
    with pytest.raises(OSError, match="FAT/exFAT") as raised:
        operations.copy_file(str(src), str(dest))

    assert raised.value.errno == errno.EPERM
    assert not isinstance(raised.value, FileExistsError)
    assert not dest.exists()
    assert not list(tmp_path.glob(".tmp_copy_*"))


def test_move_file__filesystem_without_hard_links_keeps_source(tmp_path, monkeypatch):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"photograph")

    def no_hard_links(_src, _dest):
        raise OSError(errno.EPERM, "Operation not permitted")

    monkeypatch.setattr(operations.os, "link", no_hard_links)
    with pytest.raises(OSError, match="FAT/exFAT"):
        operations.move_file(str(src), str(dest))

    assert src.read_bytes() == b"photograph"
    assert not dest.exists()


def test_hard_link__existing_destination_raises_file_exists(tmp_path):
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    src.write_bytes(b"new")
    dest.write_bytes(b"old")

    with pytest.raises(FileExistsError):
        operations._hard_link(str(src), str(dest))

    assert dest.read_bytes() == b"old"


def test_list_files__abandoned_copy_is_not_imported(tmp_path):
    """Exclude crash leftovers from later media imports."""
    (tmp_path / ".tmp_copy_abandoned").write_bytes(b"partial")
    finished = tmp_path / "finished.jpg"
    finished.write_bytes(b"complete")

    assert operations.list_files(str(tmp_path)) == [str(finished)]


def test_copy_file__killed_process_leaves_only_temporary_bytes(tmp_path):
    """Kill a real child after a partial write, bypassing Python exception cleanup."""
    src = tmp_path / "src.jpg"
    dest = tmp_path / "dest.jpg"
    ready = tmp_path / "ready"
    src.write_bytes(b"complete photograph")
    script = """
import os
from pathlib import Path
import sys
import time
sys.path.insert(0, sys.argv[1])
from shared import file_operations as operations
def partial_copy(source, temporary):
    temporary.write(b"partial")
    temporary.flush()
    os.fsync(temporary.fileno())
    Path(sys.argv[4]).write_text("ready")
    time.sleep(60)
operations.shutil.copyfileobj = partial_copy
operations.copy_file(sys.argv[2], sys.argv[3])
"""
    child = subprocess.Popen([sys.executable, "-c", script, str(PACKAGE_ROOT), str(src), str(dest), str(ready)])
    try:
        deadline = time.monotonic() + 15
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), "copy child did not reach the injected partial-write barrier"
        assert not dest.exists()
        child.kill()
        child.wait(timeout=10)
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)

    assert child.returncode != 0
    assert not dest.exists()
    leftovers = list(tmp_path.glob(".tmp_copy_*"))
    assert len(leftovers) == 1
    assert leftovers[0].read_bytes() == b"partial"
    assert str(leftovers[0]) not in operations.list_files(str(tmp_path))
    assert src.read_bytes() == b"complete photograph"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows creation-time regression")
@pytest.mark.parametrize("old_destination", ["deleted", "renamed"])
def test_copy_file__preserves_exact_creation_time_despite_tunnel_cache(tmp_path, old_destination):
    """Do not inherit the cached creation time of a recently removed destination name."""
    src = tmp_path / "source.jpg"
    dest = tmp_path / "destination.jpg"
    src.write_bytes(b"source photograph")
    dest.write_bytes(b"previous photograph")
    expected_ns = 1_650_000_000_123_456_700
    operations._set_creation_time_windows(str(src), expected_ns)
    operations._set_creation_time_windows(str(dest), 1_450_000_000_333_444_500)
    if old_destination == "deleted":
        dest.unlink()
    else:
        dest.rename(tmp_path / "previous.jpg")

    operations.copy_file(str(src), str(dest))

    assert src.stat().st_birthtime_ns == expected_ns
    assert dest.stat().st_birthtime_ns == expected_ns
    assert dest.read_bytes() == b"source photograph"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows creation-time regression")
@pytest.mark.parametrize("failure", ["exception", "wrong_time"])
def test_copy_file__creation_time_failure_prevents_publication(tmp_path, monkeypatch, failure):
    """Never report success or publish when the original creation time cannot be preserved."""
    src = tmp_path / "source.jpg"
    dest = tmp_path / "destination.jpg"
    src.write_bytes(b"photograph")
    operations._set_creation_time_windows(str(src), 1_650_000_000_123_456_700)

    def fail_creation_time(path, timestamp):
        assert Path(path) != src
        if failure == "exception":
            raise OSError("injected creation-time failure")

    monkeypatch.setattr(operations, "_set_creation_time_windows", fail_creation_time)
    with pytest.raises(OSError):
        operations.copy_file(str(src), str(dest))

    assert not dest.exists()
    assert not list(tmp_path.glob(".tmp_copy_*"))
    assert src.read_bytes() == b"photograph"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows read-only attribute")
def test_copy_file__source_is_opened_readonly_and_never_modified(tmp_path, monkeypatch):
    """Copy a read-only source; reject any attempted write access or metadata update to it."""
    src = tmp_path / "source.jpg"
    dest = tmp_path / "destination.jpg"
    src.write_bytes(b"photograph")
    operations._set_creation_time_windows(str(src), 1_650_000_000_123_456_700)
    src.chmod(stat.S_IREAD)
    before = src.stat()
    real_utime = os.utime
    real_creation_time = operations._set_creation_time_windows
    source_modes = []

    def guarded_open(path, mode="r", *args, **kwargs):
        if Path(path) == src:
            source_modes.append(mode)
            assert mode == "rb"
        return builtins.open(path, mode, *args, **kwargs)

    def guarded_utime(path, *args, **kwargs):
        assert Path(path) != src
        return real_utime(path, *args, **kwargs)

    def guarded_creation_time(path, timestamp):
        assert Path(path) != src
        return real_creation_time(path, timestamp)

    monkeypatch.setattr(operations, "open", guarded_open, raising=False)
    monkeypatch.setattr(operations.os, "utime", guarded_utime)
    monkeypatch.setattr(operations, "_set_creation_time_windows", guarded_creation_time)
    try:
        operations.copy_file(str(src), str(dest))
        after = src.stat()
        assert source_modes == ["rb"]
        assert after.st_birthtime_ns == before.st_birthtime_ns
        assert after.st_mtime_ns == before.st_mtime_ns
        assert after.st_file_attributes == before.st_file_attributes
        assert src.read_bytes() == dest.read_bytes() == b"photograph"
        assert dest.stat().st_birthtime_ns == before.st_birthtime_ns
    finally:
        src.chmod(stat.S_IREAD | stat.S_IWRITE)
