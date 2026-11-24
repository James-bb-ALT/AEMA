"""Grounded offline reading of one verified capture; never a trained forecast."""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from aema.dataset import load_dataset
from aema.errors import ParseError

ANALYSIS_SCHEMA = "1.0"
MAX_EXPANDED_BYTES = 128 * 1024 * 1024
COMPONENTS = {
    "screen": ("Tela", "screen"),
    "ambient_display": ("Tela ambiente", "screen"),
    "cpu": ("CPU", "usage"),
    "gpu": ("GPU", "usage"),
    "wifi": ("Wi-Fi", "network"),
    "mobile_radio": ("Rede móvel", "network"),
    "bluetooth": ("Bluetooth", "network"),
    "wakelock": ("Wakelocks", "usage"),
    "camera": ("Câmera", "usage"),
    "audio": ("Áudio", "usage"),
    "video": ("Vídeo", "usage"),
    "gnss": ("Localização", "usage"),
    "sensors": ("Sensores", "usage"),
    "idle": ("Repouso", None),
}
ACTIONS = {
    "screen": "Revise brilho e tempo de tela. Reduzi-los pode afetar a visibilidade e o uso.",
    "network": "Revise o uso da conexão indicada. Alterações podem afetar conectividade e sincronização.",
    "usage": "Investigue quais atividades usam esse componente antes de alterar configurações.",
    "app": "Revise o uso do aplicativo. Restrições podem atrasar notificações; o total não prova atividade em segundo plano.",
}


def _read(archive: zipfile.ZipFile, name: str, limit: int) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > limit:
        raise ParseError("capture member exceeds analysis limit")
    with archive.open(info) as stream:
        value = stream.read(limit + 1)
    if len(value) > limit:
        raise ParseError("capture member exceeds analysis limit")
    return value


def _verified_capture(path: Path):
    with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as temporary:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ParseError("duplicate capture members")
        capture = json.loads(_read(archive, "capture_manifest.json", 256 * 1024))
        if capture.get("schema_version") != "1.0":
            raise ParseError("unsupported capture schema")
        if capture.get("status") != "complete" or capture.get("parse_status") != "complete":
            raise ParseError("capture is incomplete or parsing is unsupported")
        prefix = PurePosixPath(capture["parsed_directory"])
        if prefix.is_absolute() or ".." in prefix.parts or "\\" in str(prefix):
            raise ParseError("invalid parsed directory")
        manifest_data = _read(archive, f"{prefix}/manifest.json", 256 * 1024)
        manifest = json.loads(manifest_data)
        files = manifest["files"]
        if not isinstance(files, list) or len(files) > 32:
            raise ParseError("invalid analysis artifact list")
        root = Path(temporary)
        (root / "manifest.json").write_bytes(manifest_data)
        expanded = len(manifest_data)
        for name in files:
            if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
                raise ParseError("invalid analysis artifact name")
            if name == "manifest.json":
                raise ParseError("recursive analysis manifest")
            data = _read(archive, f"{prefix}/{name}", MAX_EXPANDED_BYTES - expanded)
            expanded += len(data)
            (root / name).write_bytes(data)
        records, relations, verified = load_dataset(root)
        for source, name in (
            ("checkin", "stats.csv"),
            ("battery_report", "stats.txt"),
            ("packages", "packageUID.txt"),
        ):
            data = _read(archive, name, MAX_EXPANDED_BYTES - expanded)
            expanded += len(data)
            digest = hashlib.sha256(data).hexdigest()
            if digest != verified["input_sha256"][source].lower():
                raise ParseError("raw capture input hash mismatch")
        return capture, records, relations


def _grammar(facts: list[dict], actions: list[str]) -> str:
    def choices(values):
        return " | ".join(json.dumps(json.dumps(v)) for v in values)

    return (
        'root ::= "{\\"focus\\":[" (fact ("," fact){0,2})? '
        '"] ,\\"actions\\":[" (action ("," action){0,2})? "]}"\n'.replace("] ,", "],")
        + "fact ::= "
        + choices([f["id"] for f in facts])
        + "\n"
        + "action ::= "
        + choices(actions + ["none"])
        + "\n"
    )


def prepare_analysis(capture_path: str) -> str:
    """Build a small prompt without package names, raw logs or arbitrary payloads."""
    try:
        path = Path(capture_path)
        capture, records, relations = _verified_capture(path)
        packages: dict[int, set[str]] = {}
        for relation in relations:
            packages.setdefault(relation.uid, set()).add(relation.package_name)
        components = []
        apps = []
        total = None
        rejected = 0
        for record in records:
            if record.source.value != "power" or record.unit.value != "mAh":
                continue
            if record.value < 0:
                rejected += 1
                continue
            if record.uid is None and record.metric == "computed_drain_mah":
                total = record.value
            elif record.uid is None:
                for component, (label, action) in COMPONENTS.items():
                    if record.metric == f"{component}_estimated_charge_mah":
                        components.append(
                            dict(
                                label=label,
                                resource=component,
                                value_mah=record.value,
                                action=action,
                            )
                        )
            elif record.metric == "total_estimated_charge_mah":
                names = sorted(packages.get(record.uid, set()))
                label = " / ".join(names) if names else f"UID {record.uid} (sem pacote resolvido)"
                apps.append(
                    dict(
                        label=label[:512],
                        uid=record.uid,
                        shared_uid=len(names) > 1,
                        value_mah=record.value,
                        action="app" if record.uid % 100000 >= 10000 else None,
                    )
                )
        facts = []
        for prefix, group in (("C", components), ("A", apps)):
            for index, item in enumerate(
                sorted(group, key=lambda r: (-r["value_mah"], r["label"]))[:5], 1
            ):
                facts.append(
                    dict(
                        id=f"{prefix}{index}", axis="component" if prefix == "C" else "uid", **item
                    )
                )
        if not facts:
            raise ParseError("no component or UID charge estimates in capture")
        actions = sorted({f["action"] for f in facts if f["action"] and f["value_mah"] > 0})
        public_facts = [
            {k: f[k] for k in ("id", "axis", "value_mah", "action")}
            | ({"resource": f["resource"]} if "resource" in f else {})
            for f in facts
        ]
        prompt = (
            "Read Android battery estimates. This is a cumulative snapshot, NOT a six-hour window "
            "or a future forecast. Components and UIDs overlap: never add the axes. "
            "Select up to three useful focus IDs from the supplied facts, prioritizing positive "
            "high estimates within each axis. Select only relevant allowed actions; none means abstain. "
            "Zero estimates are not proof of zero physical consumption. "
            'Reply ONLY as {"focus":["C1"],"actions":["usage"]}. No explanation or new numbers.\n'
            + json.dumps(dict(facts=public_facts, allowed_actions=actions), separators=(",", ":"))
        )
        # Explicit streaming supports Python 3.10 as well as Android's Python 3.13.
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
        return json.dumps(
            dict(
                schema_version=ANALYSIS_SCHEMA,
                capture_sha256=hasher.hexdigest(),
                captured_at_utc=capture.get("ended_at_utc"),
                snapshot_semantics="cumulative_since_android_reset",
                forecast_status="not_trained",
                total_estimated_mah=total,
                facts=facts,
                actions=actions,
                rejected_negative_estimates=rejected,
                prompt=prompt,
                grammar=_grammar(facts, actions),
            ),
            ensure_ascii=False,
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, zipfile.BadZipFile) as exc:
        raise ParseError("capture cannot be prepared for local analysis") from exc


def validate_reading(prepared_json: str, response: str) -> str:
    """Reject ungrounded model output; human-readable facts are always inserted by code."""
    prepared = json.loads(prepared_json)
    try:
        if len(response) > 4096:
            raise ValueError("response too large")
        result = json.loads(response)
        if set(result) != {"focus", "actions"}:
            raise ValueError("unexpected fields")
        facts = {f["id"]: f for f in prepared["facts"]}
        for key, allowed in (("focus", facts), ("actions", prepared["actions"] + ["none"])):
            values = result[key]
            if (
                not isinstance(values, list)
                or len(values) > 3
                or any(not isinstance(v, str) or v not in allowed for v in values)
                or len(values) != len(set(values))
            ):
                raise ValueError("ungrounded selection")
        selected_actions = [a for a in result["actions"] if a != "none"]
        focused_actions = {facts[f]["action"] for f in result["focus"] if facts[f]["value_mah"] > 0}
        if not set(selected_actions) <= focused_actions:
            raise ValueError("action lacks selected evidence")
        return json.dumps(
            dict(
                schema_version=ANALYSIS_SCHEMA,
                mode="llm_snapshot_reading",
                forecast_status="not_trained",
                capture_sha256=prepared["capture_sha256"],
                captured_at_utc=prepared["captured_at_utc"],
                total_estimated_mah=prepared["total_estimated_mah"],
                focus=[facts[f] for f in result["focus"]],
                suggestions=[dict(id=a, text=ACTIONS[a]) for a in selected_actions],
                facts=prepared["facts"],
                rejected_negative_estimates=prepared["rejected_negative_estimates"],
            ),
            ensure_ascii=False,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise ParseError("LLM response is invalid or lacks supporting evidence") from exc
