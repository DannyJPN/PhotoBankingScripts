"""
Unit tests for exportpreparedmedia.py.
"""

import logging
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

project_root = Path(__file__).resolve().parents[3]
export_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(export_root))

import exportpreparedmedia as export_module
from exportpreparedmedialib import constants as exp_constants


def make_args(tmp_path, **overrides):
    defaults = dict(
        photo_csv=str(tmp_path / "input.csv"),
        output_dir=str(tmp_path / "out"),
        output_prefix="CSV",
        log_dir=str(tmp_path / "logs"),
        debug=False,
        overwrite=False,
        shutterstock=False,
        adobestock=False,
        dreamstime=False,
        depositphotos=False,
        bigstockphoto=False,
        _123rf=False,
        canstockphoto=False,
        pond5=False,
        gettyimages=False,
        alamy=False,
        all=False,
        include_edited=False,
        include_alternative_formats=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_is_not_edited__detects_marker():
    assert export_module._is_not_edited({"Cesta": "C:/Photos/upraven‚/img.jpg"}) is False
    assert export_module._is_not_edited({"Cesta": "C:/Photos/original/img.jpg"}) is True


def test_parse_arguments__defaults(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["exportpreparedmedia.py"])
    args = export_module.parse_arguments()

    assert args.photo_csv == exp_constants.DEFAULT_PHOTO_CSV
    assert args.output_dir == exp_constants.DEFAULT_OUTPUT_DIR
    assert args.output_prefix == exp_constants.DEFAULT_OUTPUT_PREFIX
    assert args.log_dir == exp_constants.DEFAULT_LOG_DIR
    assert args.debug is False


def test_main__all_with_individual_logs_error(monkeypatch, caplog, tmp_path):
    args = make_args(tmp_path, all=True, shutterstock=True)
    monkeypatch.setattr(export_module, "parse_arguments", lambda: args)

    with caplog.at_level(logging.ERROR):
        export_module.main()

    assert "cannot use --all" in caplog.text.lower()


def test_main__no_enabled_banks_warns(monkeypatch, caplog, tmp_path):
    args = make_args(tmp_path)
    monkeypatch.setattr(export_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(export_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(export_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(export_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(export_module, "get_enabled_banks", lambda _a: [])

    with caplog.at_level(logging.WARNING):
        export_module.main()

    assert "no banks enabled" in caplog.text.lower()


def test_main__load_csv_error_logs(monkeypatch, caplog, tmp_path):
    args = make_args(tmp_path, shutterstock=True)
    monkeypatch.setattr(export_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(export_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(export_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(export_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(export_module, "get_enabled_banks", lambda _a: ["ShutterStock"])
    monkeypatch.setattr(export_module, "get_output_paths", lambda _b, _d, _p: {"ShutterStock": "out.csv"})

    def fail_load(_p):
        raise OSError("fail")

    monkeypatch.setattr(export_module, "load_csv", fail_load)

    with caplog.at_level(logging.ERROR):
        export_module.main()

    assert "failed to load input csv" in caplog.text.lower()


def test_main__filters_edited_and_exports(monkeypatch, tmp_path):
    args = make_args(tmp_path, shutterstock=True, include_edited=False, include_alternative_formats=True)
    monkeypatch.setattr(export_module, "parse_arguments", lambda: args)
    monkeypatch.setattr(export_module, "ensure_directory", lambda _p: None)
    monkeypatch.setattr(export_module, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(export_module, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(export_module, "get_enabled_banks", lambda _a: ["ShutterStock"])
    monkeypatch.setattr(export_module, "get_output_paths", lambda _b, _d, _p: {"ShutterStock": "out.csv"})
    monkeypatch.setattr(export_module, "should_include_item", lambda _i, _b=None: True)
    monkeypatch.setattr(export_module, "load_csv", lambda _p: [
        {"Cesta": "C:/Photos/upraven‚/img.jpg"},
        {"Cesta": "C:/Photos/original/img.jpg"},
    ])

    captured = {}

    def fake_export(items, banks, output_paths, filter_func, include_alternative_formats):
        captured["items"] = items
        captured["banks"] = banks
        captured["output_paths"] = output_paths
        captured["include_alternative_formats"] = include_alternative_formats

    monkeypatch.setattr(export_module, "export_to_photobanks", fake_export)

    export_module.main()

    assert captured["banks"] == ["ShutterStock"]
    assert len(captured["items"]) == 1
    assert captured["include_alternative_formats"] is True
