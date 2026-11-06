# -*- coding: utf-8 -*-
"""OpenCAEHub PythonAdapter entrypoint (platform provides open_cae_plugin)."""
from __future__ import annotations

from pathlib import Path

from open_cae_plugin import BasePluginAdapter, run_adapter
from beam_analyzer import REPORT_NAME, VERSION as ANALYZER_VERSION, analyze_input
from input_resolver import InputResolutionError, resolve_input_file


class BeamResultVerifierAdapter(BasePluginAdapter):
    def setup(self, context):
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        print("[BeamResultVerifier] Analyzer version:", ANALYZER_VERSION)
        return {"status": "success"}

    def execute(self, context):
        ctx = context or getattr(self, "context", {}) or {}
        try:
            source = resolve_input_file(
                getattr(self, "in_param", None), ctx, self.work_dir
            )
        except InputResolutionError as exc:
            # The platform adapter turns this exception into result.json status=failed.
            print("[BeamResultVerifier] INPUT_MAPPING_ERROR:", str(exc))
            raise
        print("[BeamResultVerifier] Reading:", source.name)
        output, result = analyze_input(source, self.work_dir)
        target = Path(output)
        if not target.is_file() or target.stat().st_size <= 0:
            raise RuntimeError("Report ZIP was not generated or is empty.")

        main_dir = ctx.get("sys_main_dir")
        if not main_dir:
            raise RuntimeError("Missing sys_main_dir in PythonAdapter context.")

        # Client 2.0.14's installed BasePluginAdapter does not implement
        # _temp_relative_path, despite some sample code using that method.
        # Compute the required Client/temp-relative output path ourselves.
        temp_root = (Path(main_dir).expanduser() / "temp").resolve()
        try:
            relative = target.resolve().relative_to(temp_root).as_posix()
        except ValueError as exc:
            raise RuntimeError(
                "Report must be located under sys_main_dir/temp so that "
                "OpenCAEHub can register the output resource. "
                f"Report: {target}; temp root: {temp_root}"
            ) from exc
        print("[BeamResultVerifier] Report:", REPORT_NAME,
              "bytes:", target.stat().st_size,
              "VTU cases:", result["num_cases"])
        return {"status": "success", "filepath": relative}

    def teardown(self, context):
        return {"status": "success"}


if __name__ == "__main__":
    run_adapter(BeamResultVerifierAdapter)
