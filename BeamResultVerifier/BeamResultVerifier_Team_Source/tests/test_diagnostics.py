from pathlib import Path
import json
import tempfile
import unittest
from tools.diagnose_context import inspect_context_file


class DiagnosticsTests(unittest.TestCase):
    def test_reports_empty_input_and_legacy_plugin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=root/"result.json"
            result.write_text(json.dumps({"status":"failed","error":"empty input"}))
            context=root/"context.json"
            context.write_text(json.dumps({
                "inParam":{"inputParam":{"filepath":""}},
                "logic_command":"beamResultVerify",
                "sys_plugin_dir":str(root/"Plugins"/"BeamResultVerifier"),
                "sys_result_file":str(result),
                "outParam":{"outputParam":{"filepath":str(root/"beam_validation_report.zip")}}
            }))
            source_config=Path(__file__).resolve().parents[1]/"PluginConfig.xml"
            info=inspect_context_file(context,source_config)
            self.assertTrue(any("INPUT EMPTY" in line for line in info))
            self.assertTrue(any("differs" in line for line in info))
            self.assertTrue(any("status: failed" in line for line in info))


if __name__ == "__main__":
    unittest.main()
