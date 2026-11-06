from pathlib import Path
import tempfile
import unittest

from input_resolver import InputResolutionError, resolve_input_file


class InputResolverTests(unittest.TestCase):

    def test_project_cache_preferred_over_unscoped_other_team_temp(self):
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)
            wrong=main/"temp"/"other-team"/"case.vtu"
            wrong.parent.mkdir(parents=True)
            wrong.write_text("other")
            chosen=main/"Local"/"User-1"/"project-38"/"case.vtu"
            chosen.parent.mkdir(parents=True)
            chosen.write_text("target")
            found=resolve_input_file(
                "case.vtu",{"sys_main_dir":str(main),"sys_project_id":38}, main, env={}
            )
            self.assertEqual(found,chosen.resolve())

    def test_project_cache_does_not_pick_other_team_file(self):
        with tempfile.TemporaryDirectory() as d:
            main=Path(d)
            wrong=main/"temp"/"other-team"/"case.vtu"
            wrong.parent.mkdir(parents=True)
            wrong.write_text("other")
            with self.assertRaisesRegex(InputResolutionError,"could not be read"):
                resolve_input_file(
                    "case.vtu",{"sys_main_dir":str(main),"sys_project_id":38},main,env={}
                )

    def test_empty_context_does_not_guess_from_local_files(self):
        with tempfile.TemporaryDirectory() as d:
            main = Path(d)
            (main / "temp" / "steel").mkdir(parents=True)
            (main / "temp" / "steel" / "10mm.vtu").write_text("dummy")
            ctx = {"sys_main_dir": str(main),
                   "inParam": {"inputParam": {"filepath": ""}}}
            with self.assertRaisesRegex(InputResolutionError, "empty input"):
                resolve_input_file("", ctx, main, env={})

    def test_explicit_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "case.vtu"
            f.write_text("placeholder")
            ctx = {"inParam": {"inputParam": {"filepath": ""}}}
            found = resolve_input_file(str(f), ctx, d, env={})
            self.assertEqual(found, f.resolve())

    def test_nested_slot_filename_in_temp(self):
        with tempfile.TemporaryDirectory() as d:
            main = Path(d)
            nested = main / "temp" / "model" / "10mm" / "case.vtu"
            nested.parent.mkdir(parents=True)
            nested.write_text("placeholder")
            value = {"inputParam": {"filepath": {"type": "uri", "slot": {
                "name": "case.vtu", "type": "Resource", "uuid": "example-id"}}}}
            found = resolve_input_file(value, {"sys_main_dir": str(main)}, d, env={})
            self.assertEqual(found, nested.resolve())

    def test_ambiguous_basename_fails(self):
        with tempfile.TemporaryDirectory() as d:
            main = Path(d)
            for mesh in ("10mm", "15mm"):
                candidate = main / "temp" / mesh / "case.vtu"
                candidate.parent.mkdir(parents=True)
                candidate.write_text("placeholder")
            with self.assertRaisesRegex(InputResolutionError, "Ambiguous resource path"):
                resolve_input_file("case.vtu", {"sys_main_dir": str(main)}, d, env={})

    def test_environment_override_only_when_input_is_blank(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "selected.vtu"
            f.write_text("placeholder")
            found = resolve_input_file(
                "", {"inParam": {"inputParam": {"filepath": ""}}}, d,
                env={"BEAM_VERIFIER_INPUT_FILE": str(f)}
            )
            self.assertEqual(found, f.resolve())

    def test_nonexistent_explicit_resource_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(InputResolutionError, "could not be read"):
                resolve_input_file(
                    "missing.vtu",
                    {"sys_main_dir": d},
                    d,
                    env={}
                )


    def test_directory_hint_does_not_select_a_different_mesh(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wrong = root / "temp" / "steel" / "15mm" / "case.vtu"
            wrong.parent.mkdir(parents=True)
            wrong.write_text("placeholder")
            ctx = {"sys_main_dir": str(root)}
            with self.assertRaisesRegex(InputResolutionError, "could not be read"):
                resolve_input_file("steel/10mm/case.vtu", ctx, root, env={})

    def test_matching_relative_path_with_prefix(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            target=root/"temp"/"project"/"10mm"/"case.vtu"
            target.parent.mkdir(parents=True)
            target.write_text("placeholder")
            found=resolve_input_file("10mm/case.vtu",{"sys_main_dir":str(root)},root,env={})
            self.assertEqual(found,target.resolve())

    def test_environment_override_must_be_absolute(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(InputResolutionError, "explicit absolute"):
                resolve_input_file("",{},d,env={"BEAM_VERIFIER_INPUT_FILE":"case.vtu"})


if __name__ == "__main__":
    unittest.main()
