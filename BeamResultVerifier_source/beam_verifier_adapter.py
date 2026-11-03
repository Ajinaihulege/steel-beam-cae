# -*- coding: utf-8 -*-
"""OpenCAEHub PythonAdapter. Requires platform-provided open_cae_plugin."""
import os
from pathlib import Path
from open_cae_plugin import BasePluginAdapter, run_adapter
from beam_analyzer import analyze_team_zip

class BeamResultVerifierAdapter(BasePluginAdapter):
    def _resolve_input_file(self, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            candidates = [
                value,
                os.path.join(self.work_dir, value),
                os.path.join(self.context.get("sys_main_dir", ""), "temp", value),
            ]
            for candidate in candidates:
                if candidate and os.path.isfile(candidate):
                    return os.path.abspath(candidate)
        if isinstance(value, dict):
            for key in ("filepath", "filePath", "path", "uri", "localPath"):
                if key in value:
                    found = self._resolve_input_file(value[key])
                    if found:
                        return found
            for item in value.values():
                found = self._resolve_input_file(item)
                if found:
                    return found
        if isinstance(value, list):
            for item in value:
                found = self._resolve_input_file(item)
                if found:
                    return found
        return None

    def setup(self, context):
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)
        return {"status": "success"}

    def execute(self, context):
        source = self._resolve_input_file(self.in_param)
        if not source:
            raise FileNotFoundError("Input ZIP was not found or downloaded by ResourcePool")
        if not source.lower().endswith(".zip"):
            raise ValueError("Upload teammate's original ZIP containing both /15mm/ and /10mm/ VTU files")
        output, summary = analyze_team_zip(source, self.work_dir)
        relative = self._temp_relative_path(str(output), context.get("sys_main_dir", ""))
        print("Beam verifier completed; report:", output)
        print("Displacement change: %.4f%%" %
              summary["comparison"]["max_abs_vertical_displacement_change_percent"])
        return {"status": "success", "filepath": relative}

    def teardown(self, context):
        return {}

if __name__ == "__main__":
    run_adapter(BeamResultVerifierAdapter)
