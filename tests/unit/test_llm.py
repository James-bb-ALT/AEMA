from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pytest

import aema.llm as llm
from aema.demo import run_demo
from aema.errors import ParseError


@pytest.fixture
def capture(fixture_dir: Path, tmp_path: Path) -> Path:
    directory = Path(run_demo(fixture_dir, tmp_path / "dataset")["output_directory"])
    stage = tmp_path / "stage"
    stage.mkdir()
    shutil.copytree(directory, stage / "parsed/data")
    for source, name in (
        ("checkin_v9.csv", "stats.csv"),
        ("battery_report.txt", "stats.txt"),
        ("packages.txt", "packageUID.txt"),
    ):
        shutil.copy(fixture_dir / source, stage / name)
    (stage / "capture_manifest.json").write_text(
        json.dumps(
            dict(
                schema_version="1.0",
                status="complete",
                parse_status="complete",
                parsed_directory="parsed/data",
                ended_at_utc="2026-01-01T00:00:00Z",
            )
        ),
        encoding="utf-8",
    )
    archive = tmp_path / "capture.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        for path in stage.rglob("*"):
            if path.is_file():
                output.write(path, path.relative_to(stage).as_posix())
    return archive


def replace_member(path: Path, name: str, value: bytes) -> None:
    with zipfile.ZipFile(path) as archive:
        members = {n: archive.read(n) for n in archive.namelist()}
    members[name] = value
    with zipfile.ZipFile(path, "w") as archive:
        for member, content in members.items():
            archive.writestr(member, content)


def test_verified_capture_builds_private_bounded_grounded_prompt(capture: Path) -> None:
    prepared = json.loads(llm.prepare_analysis(str(capture)))
    assert prepared["forecast_status"] == "not_trained"
    assert prepared["snapshot_semantics"] == "cumulative_since_android_reset"
    assert len(prepared["capture_sha256"]) == 64
    assert prepared["total_estimated_mah"] == 12
    assert prepared["rejected_negative_estimates"] == 2
    assert prepared["facts"][0]["id"] == "C1"
    assert prepared["facts"][0]["label"] == "Tela"
    assert len(prepared["prompt"]) < 4000
    assert "com.example" not in prepared["prompt"]
    assert "UID 1000" not in prepared["prompt"]
    assert "root ::=" in prepared["grammar"]
    assert '"actions"' not in prepared["grammar"]
    assert "allowed_actions" not in prepared["prompt"]
    result = json.loads(llm.validate_reading(json.dumps(prepared), '{"focus":["C1"]}'))
    assert result["mode"] == "llm_snapshot_reading"
    assert result["focus"][0]["value_mah"] == 640
    assert result["suggestions"][0]["id"] == "screen"
    assert "prompt" not in result


def test_review_action_is_derived_from_selected_fact(capture: Path) -> None:
    prepared = llm.prepare_analysis(str(capture))
    result = json.loads(llm.validate_reading(prepared, '{"focus":["C1"]}'))
    assert [item["id"] for item in result["suggestions"]] == ["screen"]


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": "9"},
        {"status": "failed"},
        {"parse_status": "unsupported_or_invalid"},
        {"parsed_directory": "../escape"},
        {"parsed_directory": "/absolute"},
        {"parsed_directory": "bad\\folder"},
    ],
)
def test_rejects_incomplete_and_unsafe_capture(capture: Path, change: dict) -> None:
    with zipfile.ZipFile(capture) as archive:
        metadata = json.loads(archive.read("capture_manifest.json"))
    metadata.update(change)
    replace_member(capture, "capture_manifest.json", json.dumps(metadata).encode())
    with pytest.raises(ParseError):
        llm.prepare_analysis(str(capture))


@pytest.mark.parametrize(
    "files", [["../escape"], ["manifest.json"], ["bad\\name"], [""], list(range(33)), "not-a-list"]
)
def test_rejects_invalid_artifact_lists(capture: Path, files) -> None:
    with zipfile.ZipFile(capture) as archive:
        manifest = json.loads(archive.read("parsed/data/manifest.json"))
    manifest["files"] = files
    replace_member(capture, "parsed/data/manifest.json", json.dumps(manifest).encode())
    with pytest.raises(ParseError):
        llm.prepare_analysis(str(capture))


def test_checks_raw_hashes_as_well_as_canonical_tables(capture: Path) -> None:
    replace_member(capture, "stats.txt", b"modified")
    with pytest.raises(ParseError, match="raw capture input hash"):
        llm.prepare_analysis(str(capture))


def test_rejects_duplicate_members(capture: Path) -> None:
    with (
        pytest.warns(UserWarning, match="Duplicate name"),
        zipfile.ZipFile(capture, "a") as archive,
    ):
        archive.writestr("stats.txt", b"duplicate")
    with pytest.raises(ParseError, match="duplicate"):
        llm.prepare_analysis(str(capture))


def test_limits_expanded_payload(capture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "MAX_EXPANDED_BYTES", 100)
    with pytest.raises(ParseError, match="limit"):
        llm.prepare_analysis(str(capture))


def test_invalid_zip_and_missing_member_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "bad.zip"
    path.write_text("not zip")
    with pytest.raises(ParseError):
        llm.prepare_analysis(str(path))
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("other", b"missing")
    with pytest.raises(ParseError):
        llm.prepare_analysis(str(path))


@pytest.mark.parametrize(
    "response",
    [
        "not JSON",
        "[]",
        "{}",
        '{"focus":["C99"]}',
        '{"focus":["C1","C1"]}',
        '{"focus":"C1"}',
        '{"focus":[null]}',
        '{"focus":["C1"],"actions":["delete_system_app"]}',
        '{"focus":["C1"],"savings":95}',
        '{"focus":["C1","C1","A1","A2"]}',
        "x" * 4097,
    ],
)
def test_rejects_ungrounded_or_malformed_model_responses(capture: Path, response: str) -> None:
    with pytest.raises(ParseError, match="LLM response"):
        llm.validate_reading(llm.prepare_analysis(str(capture)), response)


def test_allows_abstention_and_none_without_recommendations(capture: Path) -> None:
    result = json.loads(llm.validate_reading(llm.prepare_analysis(str(capture)), '{"focus":[]}'))
    assert result["focus"] == result["suggestions"] == []


def test_shared_uid_is_preserved_without_exposing_packages_to_prompt(
    capture: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture_data, records, relations = llm._verified_capture(capture)
    from dataclasses import replace

    # A known positive application UID with multiple package relations.
    positive = next(r for r in records if r.metric == "total_estimated_charge_mah" and r.value > 0)
    records = [replace(positive, uid=10001)]
    monkeypatch.setattr(llm, "_verified_capture", lambda _: (capture_data, records, relations))
    prepared = json.loads(llm.prepare_analysis(str(capture)))
    assert prepared["facts"][0]["shared_uid"] is True
    assert "com.example.one / com.example.two" == prepared["facts"][0]["label"]
    assert "com.example" not in prepared["prompt"]
    assert prepared["actions"] == ["app"]


def test_no_estimates_requires_abstention(capture: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metadata, _, relations = llm._verified_capture(capture)
    monkeypatch.setattr(llm, "_verified_capture", lambda _: (metadata, [], relations))
    with pytest.raises(ParseError, match="no component"):
        llm.prepare_analysis(str(capture))
