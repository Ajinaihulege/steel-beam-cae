from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from beam_analyzer import analyze_input


def vtu_text(multiplier=1.0):
    xyz = "0 0 0  1 0 0  0 1 0  0 0 1"
    displacement = [0,0,0, 0,0,-0.01*multiplier, 0,0,-0.02*multiplier,
                    0,0,-0.03*multiplier]
    stress = [1,2,3,0,0,0] * 4
    return f"""<?xml version="1.0"?>
<VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian">
  <UnstructuredGrid>
    <Piece NumberOfPoints="4" NumberOfCells="1">
      <PointData>
        <DataArray type="Float64" Name="StaticDisplacement"
                   NumberOfComponents="3" format="ascii">{' '.join(map(str, displacement))}</DataArray>
        <DataArray type="Float64" Name="StaticStress"
                   NumberOfComponents="6" format="ascii">{' '.join(map(str, stress))}</DataArray>
      </PointData>
      <Points><DataArray type="Float64" NumberOfComponents="3" format="ascii">{xyz}</DataArray></Points>
      <Cells>
        <DataArray type="Int32" Name="connectivity" format="ascii">0 1 2 3</DataArray>
        <DataArray type="Int32" Name="offsets" format="ascii">4</DataArray>
        <DataArray type="UInt8" Name="types" format="ascii">10</DataArray>
      </Cells>
    </Piece>
  </UnstructuredGrid>
</VTKFile>
"""


class AnalyzerTests(unittest.TestCase):
    def test_single_vtu_generates_portable_report(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f = root / "case.vtu"
            f.write_text(vtu_text(), encoding="utf-8")
            output, result = analyze_input(f, root / "out")
            self.assertEqual(result["num_cases"], 1)
            self.assertTrue(Path(output).exists())
            with ZipFile(output) as bundle:
                self.assertIn("analysis_report.html", bundle.namelist())
                self.assertIn("metrics.csv", bundle.namelist())
                self.assertIn("validation.json", bundle.namelist())

    def test_two_mesh_cases_support_comparison(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            inp = root / "cases.zip"
            with ZipFile(inp, "w") as z:
                z.writestr("10mm/case.vtu", vtu_text(1.0))
                z.writestr("15mm/case.vtu", vtu_text(1.1))
            output, result = analyze_input(inp, root / "out")
            self.assertEqual(result["num_cases"], 2)
            sizes = sorted(case["mesh_size_mm"] for case in result["cases"])
            self.assertEqual(sizes, [10.0, 15.0])
            with ZipFile(output) as bundle:
                comparison = bundle.read("comparison.csv").decode("utf-8-sig")
                self.assertIn("Max |Uz| change", comparison)


if __name__ == "__main__":
    unittest.main()
