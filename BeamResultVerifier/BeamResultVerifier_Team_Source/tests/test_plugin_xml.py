from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


class PluginConfigTests(unittest.TestCase):
    def test_current_cff_binding_is_declared(self):
        root = Path(__file__).resolve().parents[1]
        cfg = ET.parse(root / "PluginConfig.xml").getroot()
        self.assertEqual(cfg.findtext("Name"), "BeamResultVerifierCommonTest")
        self.assertEqual(cfg.findtext("version"), "3.0.2.0")
        apis = cfg.findall(".//ApiInfo")
        self.assertEqual(len(apis), 1)
        self.assertEqual(apis[0].get("ModuleFullName"), "Postprocessing.PostprocessingIO")
        self.assertEqual(apis[0].get("APIName"), "BeamResultVerifierCommonTest")
        self.assertEqual(apis[0].get("AppType"), "PythonAdapter")
        self.assertEqual(apis[0].get("LogicCommand"), "beamResultVerify")
        self.assertEqual(apis[0].get("APIParameterTemlate"), "filepath=%filepath%")


if __name__ == "__main__":
    unittest.main()
