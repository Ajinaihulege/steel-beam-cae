import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from zipfile import ZipFile

from input_resolver import InputResolutionError
from test_analysis import vtu_text


def load_adapter_under_fake_platform():
    """Test adapter logic only, without claiming actual OpenCAEHub execution."""
    stub = types.ModuleType("open_cae_plugin")

    class BasePluginAdapter:
        # Deliberately NO _temp_relative_path method:
        # this reproduces the actual OpenCAEHub Client 2.0.14 error.
        pass

    stub.BasePluginAdapter = BasePluginAdapter
    stub.run_adapter = lambda adapter_class: None
    source = Path(__file__).resolve().parents[1] / "beam_verifier_adapter.py"
    previous = sys.modules.get("open_cae_plugin")
    sys.modules["open_cae_plugin"] = stub
    try:
        spec = importlib.util.spec_from_file_location("_beam_adapter_test", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.BeamResultVerifierAdapter
    finally:
        if previous is None:
            sys.modules.pop("open_cae_plugin", None)
        else:
            sys.modules["open_cae_plugin"] = previous


class AdapterContractTests(unittest.TestCase):
    def test_nonempty_filepath_returns_temp_relative_report(self):
        cls=load_adapter_under_fake_platform()
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)
            source=main/"input.vtu"
            source.write_text(vtu_text(),encoding="utf-8")
            task=main/"temp"/"38"/"task"
            task.mkdir(parents=True)
            adapter=cls()
            adapter.work_dir=str(task)
            adapter.in_param={"inputParam":{"filepath":str(source)}}
            ctx={"sys_main_dir":str(main),"sys_working_dir":str(task)}
            self.assertEqual(adapter.setup(ctx)["status"],"success")
            output=adapter.execute(ctx)
            self.assertEqual(output["status"],"success")
            self.assertEqual(output["filepath"],"38/task/beam_validation_report.zip")
            with ZipFile(task/"beam_validation_report.zip") as z:
                self.assertIn("analysis_report.html",z.namelist())


    def test_output_path_is_rejected_when_outside_temp(self):
        cls=load_adapter_under_fake_platform()
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)
            source=main/"input.vtu"
            source.write_text(vtu_text(),encoding="utf-8")
            outside=main/"outside"
            outside.mkdir()
            adapter=cls()
            adapter.work_dir=str(outside)
            adapter.in_param={"inputParam":{"filepath":str(source)}}
            ctx={"sys_main_dir":str(main),"sys_working_dir":str(outside)}
            with self.assertRaisesRegex(RuntimeError,"Report must be located under"):
                adapter.execute(ctx)

    def test_blank_filepath_does_not_generate_fresh_report(self):
        cls=load_adapter_under_fake_platform()
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)
            task=main/"temp"/"38"/"task"
            task.mkdir(parents=True)
            adapter=cls()
            adapter.work_dir=str(task)
            adapter.in_param={"inputParam":{"filepath":""}}
            ctx={"sys_main_dir":str(main),"sys_working_dir":str(task)}
            with self.assertRaisesRegex(InputResolutionError,"empty input"):
                adapter.execute(ctx)
            self.assertFalse((task/"beam_validation_report.zip").exists())


if __name__ == "__main__":
    unittest.main()
