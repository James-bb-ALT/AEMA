"""Host-side intake metadata for already collected input files."""

from __future__ import annotations

from aema.files import sha256_file
from aema.models import PipelineInputs


def describe_inputs(inputs: PipelineInputs) -> tuple[dict[str, str], dict[str, str]]:
    """Return stable source hashes and resolved paths for a parsed session."""
    sources = {
        "checkin": inputs.checkin,
        "battery_report": inputs.battery_report,
        "packages": inputs.packages,
    }
    hashes = {name: sha256_file(path) for name, path in sources.items()}
    paths = {name: str(path.resolve()) for name, path in sources.items()}
    return hashes, paths
