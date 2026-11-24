"""Audit planned trials and exclusions before descriptive analysis."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from aema.errors import AemaError, ParseError
from aema.files import sha256_file
from aema.validation import analyze_trials


def audit_study(protocol_path: str | Path, trials_path: str | Path) -> dict:
    """Require the observed trial ledger to match a frozen study plan."""
    try:
        protocol = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
        if protocol["status"] != "frozen" or not protocol["protocol_id"]:
            raise ParseError("study protocol must be frozen and identified")
        planned = protocol["planned_trials"]
        if not isinstance(planned, dict) or not planned:
            raise ParseError("planned_trials must be a non-empty mapping")
        allowed = protocol["allowed_exclusion_reasons"]
        if not isinstance(allowed, list) or any(not isinstance(item, str) for item in allowed):
            raise ParseError("allowed_exclusion_reasons must be a list of strings")
        expected = {}
        for condition, trial_ids in planned.items():
            if not condition or not isinstance(trial_ids, list) or not trial_ids:
                raise ParseError("each condition needs planned trial IDs")
            for trial_id in trial_ids:
                if not isinstance(trial_id, str) or not trial_id or trial_id in expected:
                    raise ParseError("planned trial IDs must be unique and non-empty")
                expected[trial_id] = condition
        with Path(trials_path).open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None or not {
                "trial_id",
                "condition",
                "exclusion_reason",
            } <= set(reader.fieldnames):
                raise ParseError("trial ledger is missing audit columns")
            observed = {}
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ParseError("malformed trial ledger row")
                trial_id = row["trial_id"]
                if not trial_id or trial_id in observed:
                    raise ParseError("trial ledger has missing or duplicate trial ID")
                observed[trial_id] = row
        if set(observed) != set(expected):
            raise ParseError("trial ledger differs from the frozen plan")
        exclusions = []
        for trial_id, row in observed.items():
            if row["condition"] != expected[trial_id]:
                raise ParseError(f"condition differs from plan for {trial_id}")
            reason = row["exclusion_reason"].strip()
            if reason:
                if reason not in allowed:
                    raise ParseError(f"unplanned exclusion reason for {trial_id}")
                exclusions.append({"trial_id": trial_id, "reason": reason})
        analysis = analyze_trials(trials_path)
        return {
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": sha256_file(Path(protocol_path)),
            "trials_sha256": sha256_file(Path(trials_path)),
            "planned_trial_count": len(expected),
            "exclusions": sorted(exclusions, key=lambda item: item["trial_id"]),
            "analysis": analysis,
        }
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, csv.Error) as exc:
        raise ParseError(f"invalid study inputs: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a frozen charge study")
    parser.add_argument("protocol_json", type=Path)
    parser.add_argument("trials_csv", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_study(args.protocol_json, args.trials_csv)
    except AemaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
