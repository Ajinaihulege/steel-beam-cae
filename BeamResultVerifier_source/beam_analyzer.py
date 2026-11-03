# -*- coding: utf-8 -*-
"""Beam VTU verifier v1.0; no third-party dependencies.
Inputs: the teammate's ZIP containing /15mm/ and /10mm/ VTU files.
Outputs: metrics.csv, validation.json, report.html, report.zip.
Limitations: ASCII UnstructuredGrid VTU only; static linear elastic case.
"""
import argparse
import csv
import html
import io
import json
import math
import zipfile
from array import array
from pathlib import Path
import xml.etree.ElementTree as ET

VERSION = "1.0.0"
E_MPA = 206000.0
LOAD_N = 20000.0
SPAN_MM = 4000.0
WIDTH_MM = 200.0
HEIGHT_MM = 200.0
WEB_MM = 8.0
FLANGE_MM = 12.0

def parse_vtu(stream, mesh_label):
    """Read relevant numeric fields with stdlib only; do not rely on ParaView."""
    data, tags = {}, []
    piece_attrs = None
    for event, el in ET.iterparse(stream, events=("start", "end")):
        tag = el.tag.rsplit("}", 1)[-1]
        if event == "start":
            tags.append(tag)
            if tag == "Piece":
                piece_attrs = dict(el.attrib)
        else:
            if tag == "DataArray" and len(tags) >= 2:
                group = tags[-2]
                name = el.get("Name", "")
                key = (group, name)
                want = key in {
                    ("Points", "Points"),
                    ("PointData", "StaticDisplacement"),
                    ("PointData", "StaticStress"),
                    ("Cells", "types"),
                }
                if want:
                    if el.get("format", "ascii").lower() != "ascii":
                        raise ValueError("V1 supports ASCII VTU only; export ASCII VTU in ParaView.")
                    if el.text is None:
                        raise ValueError(f"DataArray {name} is empty")
                    if key == ("Cells", "types"):
                        data[key] = array("I", map(int, el.text.split()))
                    else:
                        data[key] = array("d", map(float, el.text.split()))
                    data[(group, name, "ncomp")] = int(el.get("NumberOfComponents", "1"))
            el.clear()
            tags.pop()

    if not piece_attrs:
        raise ValueError("VTU has no Piece metadata")
    nn = int(piece_attrs.get("NumberOfPoints", 0))
    nc = int(piece_attrs.get("NumberOfCells", 0))
    def required(group, name, components):
        key = (group, name)
        if key not in data:
            raise ValueError(f"Missing array: {group}/{name}")
        if data.get((group, name, "ncomp")) != components:
            raise ValueError(f"Array {name} is not {components}-component")
        if len(data[key]) != nn * components:
            raise ValueError(f"Array length mismatch for {name}")
        if not all(math.isfinite(v) for v in data[key]):
            raise ValueError(f"Invalid NaN/Inf values in {name}")
        return data[key]

    if nn < 1 or nc < 1:
        raise ValueError("Point/cell counts must be positive")
    xyz = required("Points", "Points", 3)
    disp = required("PointData", "StaticDisplacement", 3)
    stress = required("PointData", "StaticStress", 6)
    cell_types = data.get(("Cells", "types"))
    if cell_types is None or len(cell_types) != nc:
        raise ValueError("Missing/mismatched VTK cell type array")

    max_dmag = -1.0
    max_dz_abs = -1.0
    max_dz_abs_point = None
    max_dmag_point = None
    z_min, z_max = float("inf"), float("-inf")
    x_min, x_max = float("inf"), float("-inf")
    stress0_abs_max = 0.0
    s0_min, s0_max = float("inf"), float("-inf")
    for i in range(nn):
        a, b, c = disp[3*i:3*i+3]
        vmag = math.sqrt(a*a + b*b + c*c)
        if vmag > max_dmag:
            max_dmag = vmag
            max_dmag_point = i
        if abs(c) > max_dz_abs:
            max_dz_abs, max_dz_abs_point = abs(c), i
        z_min, z_max = min(z_min, c), max(z_max, c)
        x = xyz[3*i]
        x_min, x_max = min(x_min, x), max(x_max, x)
        s0 = stress[6*i]
        s0_min, s0_max = min(s0_min, s0), max(s0_max, s0)
        stress0_abs_max = max(stress0_abs_max, abs(s0))
    return {
        "mesh_label": mesh_label,
        "points": nn,
        "cells": nc,
        "tetra_cells": sum(1 for ct in cell_types if ct == 10),
        "all_tetra": all(ct == 10 for ct in cell_types),
        "max_displacement_magnitude_mm": max_dmag,
        "max_abs_vertical_displacement_mm": max_dz_abs,
        "min_vertical_displacement_mm": z_min,
        "max_vertical_displacement_mm": z_max,
        "max_displacement_point_index_zero_based": max_dmag_point,
        "max_abs_vertical_point_index_zero_based": max_dz_abs_point,
        "max_abs_vertical_point_x_mm": xyz[3*max_dz_abs_point],
        "stress_component_0_min": s0_min,
        "stress_component_0_max": s0_max,
        "stress_component_0_abs_max": stress0_abs_max,
        "x_coord_min_mm": x_min,
        "x_coord_max_mm": x_max,
        "units_assumed": "mm, N, MPa (assumed from teammate model, not encoded in VTU)",
    }

def _find_vtu_in_team_zip(z):
    groups = {15: [], 10: []}
    for n in z.namelist():
        normalized = n.replace("\\", "/").lower()
        if not normalized.endswith(".vtu"):
            continue
        if "/15mm/" in normalized:
            groups[15].append(n)
        if "/10mm/" in normalized:
            groups[10].append(n)
    for size in groups:
        if len(groups[size]) != 1:
            raise ValueError(
                f"Expected exactly one VTU inside /{size}mm/ folder, found {len(groups[size])}"
            )
    return groups[15][0], groups[10][0]

def _percentage_change(a, b):
    return abs(a-b) / abs(b) * 100 if b else None

def analyze_team_zip(input_zip, output_dir):
    input_zip = Path(input_zip)
    output_dir = Path(output_dir)
    if not input_zip.is_file():
        raise FileNotFoundError(input_zip)
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_zip) as z:
        a_path, b_path = _find_vtu_in_team_zip(z)
        with z.open(a_path) as f:
            a = parse_vtu(f, "15 mm")
        with z.open(b_path) as f:
            b = parse_vtu(f, "10 mm")
    return create_report(a, b, output_dir, provenance=input_zip.name)

def analyze_two_vtu(vtu15, vtu10, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(vtu15, "rb") as f:
        a = parse_vtu(f, "15 mm")
    with open(vtu10, "rb") as f:
        b = parse_vtu(f, "10 mm")
    return create_report(a, b, output_dir, provenance=f"{Path(vtu15).name}; {Path(vtu10).name}")

def create_report(a, b, output_dir, provenance):
    displacement_delta = _percentage_change(
        a["max_abs_vertical_displacement_mm"], b["max_abs_vertical_displacement_mm"])
    stress0_delta = _percentage_change(
        a["stress_component_0_abs_max"], b["stress_component_0_abs_max"])
    I = (WIDTH_MM * HEIGHT_MM**3 -
         (WIDTH_MM-WEB_MM) * (HEIGHT_MM-2*FLANGE_MM)**3) / 12.0
    theory = LOAD_N * SPAN_MM**3 / (48.0 * E_MPA * I)
    error15 = _percentage_change(a["max_abs_vertical_displacement_mm"], theory)
    error10 = _percentage_change(b["max_abs_vertical_displacement_mm"], theory)
    checks = [
        {"name":"VTU arrays readable", "status":"PASS",
         "detail":"Coordinates, displacement, and six stress components were read and contain finite values."},
        {"name":"Tetrahedral mesh type", "status":"PASS" if a["all_tetra"] and b["all_tetra"] else "REVIEW",
         "detail":"All cells should be VTK_TETRA (type 10) for this team's volume meshes."},
        {"name":"Two-mesh displacement sensitivity",
         "status":"PRELIMINARY PASS" if displacement_delta <= 1.0 else "REVIEW",
         "detail":f"Change = {displacement_delta:.4f}%; threshold of 1.0% is a reporting criterion, not proof of physical accuracy."},
        {"name":"Theory comparison", "status":"REVIEW",
         "detail":f"Idealized simply supported Euler-Bernoulli result = {theory:.4f} mm. "
                  f"FEA differences = {error15:.2f}% (15 mm) and {error10:.2f}% (10 mm); "
                  "supports and load discretization may differ from ideal theory."},
        {"name":"Stress convergence", "status":"NOT ESTABLISHED",
         "detail":f"Stress component 0 absolute peak change = {stress0_delta:.2f}%; "
                  "component ordering and localized peaks must be checked; component 0 is NOT automatically von Mises."},
    ]
    report = {
        "tool":"BeamResultVerifier", "version":VERSION, "source":provenance,
        "mesh_15mm":a, "mesh_10mm":b,
        "comparison":{"max_abs_vertical_displacement_change_percent":displacement_delta,
                      "stress_component_0_abs_peak_change_percent":stress0_delta},
        "ideal_beam_reference":{"assumptions":"Simply supported Euler-Bernoulli, central point load, H-section dimensions from teammate",
                                "second_moment_mm4":I, "max_deflection_mm":theory,
                                "fe_vs_theory_percent":{"15mm":error15,"10mm":error10}},
        "checks":checks,
        "limitations":[
            "Input results are from the teammate and are not newly solved by this tool.",
            "VTU does not encode trustworthy physical units; mm/N/MPa are assumed from the model.",
            "StaticStress has six unlabeled components; component 0 must not be presented as von Mises stress.",
            "Two mesh sizes establish only preliminary displacement stability, not general convergence or solution correctness.",
            "Boundary conditions, total force, solver log and constitutive model cannot be verified from VTU alone."
        ]
    }
    j = output_dir / "validation.json"
    j.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
      ("Nodes", "points"), ("Tetrahedral elements", "tetra_cells"),
      ("Max displacement magnitude (mm)", "max_displacement_magnitude_mm"),
      ("Max abs vertical displacement (mm)", "max_abs_vertical_displacement_mm"),
      ("Min vertical displacement (mm)", "min_vertical_displacement_mm"),
      ("Stress component 0 abs max (units assumed MPa)", "stress_component_0_abs_max"),
    ]
    c = output_dir / "metrics.csv"
    with c.open("w", encoding="utf-8-sig", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(["Metric", "15 mm", "10 mm"])
        for title, key in fields:
            writer.writerow([title, a[key], b[key]])
        writer.writerow(["Vertical displacement change (%)", "", displacement_delta])
        writer.writerow(["Stress component 0 abs peak change (%)", "", stress0_delta])
        writer.writerow(["Ideal beam deflection (mm)", theory, theory])

    def fnum(v, digits=4):
        return f"{v:,.{digits}f}"
    pass_count = sum(ck["status"].startswith("PASS") or ck["status"] == "PRELIMINARY PASS" for ck in checks)
    table_rows = "\n".join(
        f"<tr><td>{html.escape(title)}</td><td>{fnum(a[key]) if isinstance(a[key],float) else a[key]:}</td>"
        f"<td>{fnum(b[key]) if isinstance(b[key],float) else b[key]:}</td></tr>"
        for title, key in fields
    )
    check_rows = "\n".join(
        f"<tr><td>{html.escape(ch['name'])}</td><td>{html.escape(ch['status'])}</td>"
        f"<td>{html.escape(ch['detail'])}</td></tr>" for ch in checks)
    width_a = round(100 * a["max_abs_vertical_displacement_mm"] /
                    max(a["max_abs_vertical_displacement_mm"], b["max_abs_vertical_displacement_mm"]), 3)
    width_b = round(100 * b["max_abs_vertical_displacement_mm"] /
                    max(a["max_abs_vertical_displacement_mm"], b["max_abs_vertical_displacement_mm"]), 3)
    doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>Beam Results Validation · v{VERSION}</title>
<style>
body{{font-family:Arial,'Microsoft YaHei',sans-serif;color:#233747;background:#f6f8fa;margin:0;}}
main{{max-width:970px;margin:30px auto;padding:30px;background:#fff;border:1px solid #dae3e8;border-radius:12px;}}
h1{{font-size:26px;margin:4px 0}} h2{{margin-top:28px;font-size:18px;border-bottom:1px solid #e1e7ec;padding-bottom:9px}}
p{{line-height:1.75}} .sub{{color:#587080}} .kpi{{display:flex;gap:16px;flex-wrap:wrap}}
.kpi div{{border:1px solid #dce5eb;border-radius:8px;padding:12px 20px;min-width:170px}}
.kpi b{{font-size:22px;display:block;color:#234a62}}
table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}}
th,td{{border-bottom:1px solid #e1e8ed;padding:11px;text-align:left;vertical-align:top}}
th{{background:#f2f6f8}} .bar{{height:18px;background:#5589a5;border-radius:3px}}
.warn{{background:#fff9ed;border-left:3px solid #cf9636;padding:11px 15px;}}
small{{color:#647989}} code{{background:#edf3f5;padding:2px 5px}}
</style></head><body><main>
<small>BeamResultVerifier / v{VERSION} · 自研结果验证原型</small>
<h1>工字钢梁仿真结果自动分析</h1>
<p class="sub">输入来自队友已有的 VTU 计算结果；本工具不重新计算有限元模型。</p>
<div class="kpi">
<div><small>15 mm / max |Uz|</small><b>{fnum(a['max_abs_vertical_displacement_mm'])} mm</b></div>
<div><small>10 mm / max |Uz|</small><b>{fnum(b['max_abs_vertical_displacement_mm'])} mm</b></div>
<div><small>Relative change</small><b>{fnum(displacement_delta,3)}%</b></div>
</div>
<h2>Displacement comparison</h2>
<p>15 mm · {fnum(a['max_abs_vertical_displacement_mm'])} mm</p>
<div class="bar" style="width:{width_a}%"></div>
<p>10 mm · {fnum(b['max_abs_vertical_displacement_mm'])} mm</p>
<div class="bar" style="width:{width_b}%"></div>
<h2>数值汇总</h2><table><thead><tr><th>Metric</th><th>15 mm</th><th>10 mm</th></tr></thead><tbody>{table_rows}</tbody></table>
<h2>自动检查与判断边界</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Interpretation</th></tr></thead>
<tbody>{check_rows}</tbody></table>
<h2>理论参考</h2>
<p>把钢梁简化为两端简支、跨中受 20 kN 集中力的 Euler-Bernoulli 梁：
跨中理论挠度约 <b>{fnum(theory)} mm</b>，
与 15 mm/10 mm 数据分别相差 <b>{fnum(error15,2)}%</b> 和 <b>{fnum(error10,2)}%</b>。
该模型忽略局部载荷分布和三维支座效应，因此只是理论参考。</p>
<p class="warn"><b>不能自动保证“物理正确”。</b> 现有 VTU 仅能验证数值结构、计算结果大小及网格敏感性。
材料、真实载荷、支座定义与求解器收敛日志仍需回到 INP/原始工程文件检查。
两个网格的位移很接近，但局部应力峰值尚未证明收敛。</p>
<h2>附加数据</h2><p>同一报告包中包含 <code>metrics.csv</code> 与 <code>validation.json</code>，
后续可作为炎核平台节点的标准输出。</p>
<small>Source: {html.escape(provenance)} | Units assumed: mm, N, MPa | Generated by BeamResultVerifier v{VERSION}</small>
</main></body></html>"""
    h = output_dir / "analysis_report.html"
    h.write_text(doc, encoding="utf-8")
    zpath = output_dir / "beam_validation_report.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in (h, c, j):
            z.write(file, file.name)
    return zpath, report

def main():
    parser = argparse.ArgumentParser(description="Validate 15/10mm steel beam VTU results")
    parser.add_argument("--team-zip", help="Team zip containing /15mm/ and /10mm/ VTU")
    parser.add_argument("--vtu15", help="15 mm result")
    parser.add_argument("--vtu10", help="10 mm result")
    parser.add_argument("--output-dir", default="report_output")
    args = parser.parse_args()
    if args.team_zip:
        output, report = analyze_team_zip(args.team_zip, args.output_dir)
    elif args.vtu15 and args.vtu10:
        output, report = analyze_two_vtu(args.vtu15, args.vtu10, args.output_dir)
    else:
        parser.error("Use --team-zip FILE or --vtu15 FILE --vtu10 FILE")
    print("Report ZIP:", output)
    print("Vertical displacement change: {:.4f}%".format(
        report["comparison"]["max_abs_vertical_displacement_change_percent"]))

if __name__ == "__main__":
    main()
