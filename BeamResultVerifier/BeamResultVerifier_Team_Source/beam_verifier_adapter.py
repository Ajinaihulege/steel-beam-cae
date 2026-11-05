# -*- coding: utf-8 -*-
"""OpenCAEHub PythonAdapter entrypoint (platform provides open_cae_plugin)."""
from __future__ import annotations

from pathlib import Path

from open_cae_plugin import BasePluginAdapter, run_adapter
from beam_analyzer import REPORT_NAME, VERSION as ANALYZER_VERSION, analyze_input
from input_resolver import resolve_input_file


class BeamResultVerifierAdapter(BasePluginAdapter):
    def setup(self, context):
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        print("[BeamResultVerifier] Analyzer version:", ANALYZER_VERSION)
        return {"status": "success"}

    def execute(self, context):
        ctx = context or getattr(self, "context", {}) or {}
        source = resolve_input_file(
            getattr(self, "in_param", None), ctx, self.work_dir
        )
        print("[BeamResultVerifier] Reading:", source.name)
        output, result = analyze_input(source, self.work_dir)
        target = Path(output)
        if not target.is_file() or target.stat().st_size <= 0:
            raise RuntimeError("Report ZIP was not generated or is empty.")

        main_dir = ctx.get("sys_main_dir")
        if not main_dir:
            raise RuntimeError("Missing sys_main_dir in PythonAdapter context.")

        # The platform expects a relative path under Client/temp.
        relative = self._temp_relative_path(str(target), main_dir)
        print("[BeamResultVerifier] Report:", REPORT_NAME,
              "bytes:", target.stat().st_size,
              "VTU cases:", result["num_cases"])
        return {"status": "success", "filepath": relative}

    def teardown(self, context):
        return {"status": "success"}


if __name__ == "__main__":
    run_adapter(BeamResultVerifierAdapter)
