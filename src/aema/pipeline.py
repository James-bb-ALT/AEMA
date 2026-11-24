"""Application orchestration for the three supported AEMA inputs."""

from __future__ import annotations

from aema.acquisition import describe_inputs
from aema.models import PipelineInputs, PipelineResult
from aema.parsers.battery_report import BatteryReportParser
from aema.parsers.checkin import CheckinParser
from aema.parsers.packages import PackageUidParser


def run_pipeline(inputs: PipelineInputs, *, strict: bool = True) -> PipelineResult:
    """Validate and parse every input, returning data without writing files."""

    checkin = CheckinParser(inputs.checkin, strict=strict).parse_result()
    battery_report = BatteryReportParser(inputs.battery_report, strict=strict).parse_result()
    packages = PackageUidParser(inputs.packages, strict=strict).parse_result()
    hashes, paths = describe_inputs(inputs)
    return PipelineResult(checkin, battery_report, packages, hashes, paths)


parse_inputs = run_pipeline
