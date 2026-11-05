# -*- coding: utf-8 -*-
"""BeamResultVerifier 3.0 - standalone VTU analysis and OpenCAEHub plugin core.

Accepts a single ASCII UnstructuredGrid VTU, or a ZIP containing 1-30 VTUs.
Reports data-level validity, displacement/stress metrics, mesh sensitivity,
optional explicit benchmark comparison, and a portable HTML/CSV/JSON bundle.

No finite-element solve is performed. No claim of safety or physical correctness.
Requires only Python >= 3.11 standard library.
"""
from __future__ import annotations

import argparse
from array import array
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import time
import xml.etree.ElementTree as ET
import zipfile

VERSION = "3.0.0"
REPORT_NAME = "beam_validation_report.zip"
MAX_VTU_FILES = 30
MAX_VTU_BYTES = 700 * 1024 * 1024
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_POINTS = 2_000_000
DISP_NAMES = {"staticdisplacement", "displacement", "u", "displacements"}
STRESS_NAMES = {"staticstress", "stress", "s"}
VM_NAMES = {"vonmises", "mises", "von_mises", "staticmises", "smises"}
VOIGT_NEEDED = {"xx", "yy", "zz", "xy", "yz", "xz"}

class AnalysisError(ValueError):
    """An input or data validation problem with an actionable error message."""

def _tag(el):
    return el.tag.rsplit("}", 1)[-1]

def _read_array(el, integer=False):
    fmt = el.get("format", "ascii").strip().lower()
    if fmt != "ascii":
        raise AnalysisError(
            "VTU DataArray uses binary/appended encoding. "
            "This portable version handles ASCII VTU. "
            "In ParaView use Save Data, set file type .vtu and Data Mode = ASCII."
        )
    content = el.text or ""
    if not content.strip():
        return array("I") if integer else array("d")
    try:
        return array("I" if integer else "d",
                     (int(t) if integer else float(t) for t in content.split()))
    except (OverflowError, ValueError) as exc:
        raise AnalysisError("VTU contains a non-numeric DataArray entry.") from exc

def _is_finite(values):
    return all(math.isfinite(x) for x in values)

def _percent_delta(coarse, fine):
    if fine == 0:
        return None
    return abs(coarse - fine) / abs(fine) * 100.0

def _nearest_quantile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round(q * (len(ordered) - 1))]

def _hash_stream(f):
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()

def _von_mises(comp):
    sxx, syy, szz, sxy, syz, sxz = comp
    return math.sqrt(max(0.0, ((sxx-syy)**2 + (syy-szz)**2 + (szz-sxx)**2)/2
                              + 3*(sxy*sxy + syz*syz + sxz*sxz)))

def _validate_voigt(order):
    if order is None:
        return None
    if (not isinstance(order, list) or len(order) != 6 or
            set(order) != VOIGT_NEEDED):
        raise AnalysisError(
            'stress_voigt_order must be exactly six unique labels: '
            '["xx","yy","zz","xy","yz","xz"] in actual file component order.'
        )
    return [order.index(key) for key in ("xx","yy","zz","xy","yz","xz")]

def parse_vtu(stream, source_name, config=None):
    """Parse a single-piece ASCII VTU without loading XML wholesale."""
    config = config or {}
    voigt_positions = _validate_voigt(config.get("stress_voigt_order"))
    fields = {}
    metadata = {}
    found_piece_count = 0
    point_arrays = []
    stack = []
    for event, el in ET.iterparse(stream, events=("start", "end")):
        tag = _tag(el)
        if event == "start":
            stack.append(tag)
            if tag == "Piece":
                found_piece_count += 1
                if found_piece_count > 1:
                    raise AnalysisError("Multi-piece VTU not supported in v3; merge blocks in ParaView first.")
                metadata = dict(el.attrib)
                if int(metadata.get("NumberOfPoints", "0")) > MAX_POINTS:
                    raise AnalysisError("VTU has too many points for the portable memory limit.")
            continue
        if tag == "DataArray" and len(stack) >= 2:
            group = stack[-2]
            name = (el.get("Name") or "").strip()
            low = name.lower()
            ncomp = int(el.get("NumberOfComponents", "1"))
            role = None
            if group == "Points" and "points" not in fields:
                role = "points"
            elif group == "Cells" and low == "types":
                role = "types"
            elif group == "PointData":
                point_arrays.append({"name": name, "components": ncomp})
                if low in DISP_NAMES and ncomp == 3 and "displacement" not in fields:
                    role = "displacement"
                elif low in STRESS_NAMES and ncomp in (1, 6) and "stress" not in fields:
                    role = "stress"
                elif low in VM_NAMES and ncomp == 1 and "mises" not in fields:
                    role = "mises"
            if role:
                values = _read_array(el, integer=(role == "types"))
                fields[role] = (values, ncomp, name)
        el.clear()
        stack.pop()
    if found_piece_count != 1:
        raise AnalysisError("Not a supported single-piece VTK UnstructuredGrid file.")
    n = int(metadata.get("NumberOfPoints", 0))
    cells = int(metadata.get("NumberOfCells", 0))
    if n <= 0 or cells <= 0:
        raise AnalysisError("VTU has no mesh points or cells.")
    if "points" not in fields or len(fields["points"][0]) != 3*n:
        raise AnalysisError("VTU Points array is missing or not 3-component XYZ.")
    if "types" not in fields or len(fields["types"][0]) != cells:
        raise AnalysisError("VTU Cells/types array is missing or has wrong length.")
    if "displacement" not in fields or len(fields["displacement"][0]) != 3*n:
        raise AnalysisError("VTU PointData requires a 3-vector named StaticDisplacement, U or Displacement.")
    xyz = fields["points"][0]
    u = fields["displacement"][0]
    if not _is_finite(xyz) or not _is_finite(u):
        raise AnalysisError("Coordinates/displacements contain NaN or infinity.")

    stress = fields.get("stress")
    if stress is not None:
        stress_a, stress_ncomp, stress_name = stress
        if len(stress_a) != stress_ncomp*n or not _is_finite(stress_a):
            raise AnalysisError("Stress array has wrong length or NaN/Inf values.")
    mises_a = fields.get("mises")
    if mises_a is not None:
        if len(mises_a[0]) != n or not _is_finite(mises_a[0]):
            raise AnalysisError("von Mises scalar array has wrong length or NaN/Inf values.")

    xmax, xmin = -math.inf, math.inf
    ymin, ymax = math.inf, -math.inf
    zmin, zmax = math.inf, -math.inf
    max_disp = -math.inf
    max_abs_uz = -math.inf
    max_disp_node = None
    max_uz_node = None
    min_uz, max_uz = math.inf, -math.inf
    all_umag, all_abs_uz = [], []
    near_zero = 0
    for i in range(n):
        x, y, z = xyz[3*i:3*i+3]
        ux, uy, uz = u[3*i:3*i+3]
        mag = math.sqrt(ux*ux + uy*uy + uz*uz)
        all_umag.append(mag)
        all_abs_uz.append(abs(uz))
        if mag <= 1e-10:
            near_zero += 1
        if mag > max_disp:
            max_disp, max_disp_node = mag, i
        if abs(uz) > max_abs_uz:
            max_abs_uz, max_uz_node = abs(uz), i
        min_uz, max_uz = min(min_uz, uz), max(max_uz, uz)
        xmin, xmax = min(xmin, x), max(xmax, x)
        ymin, ymax = min(ymin, y), max(ymax, y)
        zmin, zmax = min(zmin, z), max(zmax, z)

    out = {
        "source": source_name,
        "points": n,
        "cells": cells,
        "tetra_cells": sum(1 for kind in fields["types"][0] if kind == 10),
        "all_tetra": all(kind == 10 for kind in fields["types"][0]),
        "available_point_arrays": point_arrays,
        "displacement_array": fields["displacement"][2],
        "bounds": {"xmin": xmin, "xmax": xmax, "ymin": ymin,
                   "ymax": ymax, "zmin": zmin, "zmax": zmax},
        "max_displacement_magnitude": max_disp,
        "max_abs_vertical_displacement": max_abs_uz,
        "minimum_vertical_displacement": min_uz,
        "maximum_vertical_displacement": max_uz,
        "p95_abs_vertical_displacement": _nearest_quantile(all_abs_uz, 0.95),
        "p99_displacement_magnitude": _nearest_quantile(all_umag, 0.99),
        "near_zero_displacement_points": near_zero,
        "max_displacement_point_id_zero_based": max_disp_node,
        "max_abs_vertical_point_id_zero_based": max_uz_node,
        "max_abs_vertical_point_xyz": list(xyz[3*max_uz_node:3*max_uz_node+3]),
        "stress": None,
    }
    if stress:
        va, count, name = stress
        by_component = []
        for j in range(count):
            col = va[j::count]
            by_component.append({
                "index": j, "minimum": min(col), "maximum": max(col),
                "maximum_absolute": max(abs(v) for v in col)
            })
        out["stress"] = {
            "array": name, "components": count,
            "component_stats": by_component,
            "note": "Component indices are unlabeled; do not call component 0 von Mises."
        }
        if voigt_positions is not None and count == 6:
            vm_max = 0.0
            for i in range(n):
                components = [va[6*i + k] for k in voigt_positions]
                vm_max = max(vm_max, _von_mises(components))
            out["stress"]["mises_from_explicit_voigt_order"] = vm_max
    if mises_a:
        out["mises_scalar"] = {"array": mises_a[2], "maximum": max(mises_a[0])}
    elif stress and voigt_positions is None:
        out["mises_scalar"] = None
    return out

def _case_metadata(name, config):
    normalized = name.replace("\\", "/")
    defaults = {
        "label": Path(normalized).stem,
        "mesh_size_mm": None, "load_N": None,
    }
    matches = re.findall(r"(?<![0-9])([0-9]+(?:\.[0-9]+)?)\s*mm(?:/|\\|_|\b)", normalized, re.I)
    if matches:
        defaults["mesh_size_mm"] = float(matches[0])
    for pattern, item in (config.get("cases") or {}).items():
        if not isinstance(item, dict):
            continue
        if normalized.lower().endswith(str(pattern).replace("\\", "/").lower()):
            defaults.update({k: v for k,v in item.items()
                             if k in ("label", "mesh_size_mm", "load_N")})
            break
    return defaults

def _load_config(data):
    if isinstance(data, dict):
        result = data
    else:
        try:
            result = json.loads(data)
        except (ValueError, TypeError) as exc:
            raise AnalysisError("Config is not valid UTF-8 JSON.") from exc
    if not isinstance(result, dict):
        raise AnalysisError("Config must contain a JSON object.")
    if "cases" in result and not isinstance(result["cases"], dict):
        raise AnalysisError("Config 'cases' must be a name-to-settings object.")
    _validate_voigt(result.get("stress_voigt_order"))
    return result

def _settings_checks(items, config):
    checks = [
        {
            "check": "VTU numerical structure",
            "status": "PASS",
            "note": "Each VTU has mesh topology, valid point coordinates and finite 3-D displacements."
        },
        {
            "check": "Finite-element solution provenance",
            "status": "NOT_VERIFIED",
            "note": "VTU alone does not verify loads, materials, support DOFs or solver convergence."
        },
    ]
    if any(not item["all_tetra"] for item in items):
        checks.append({"check": "Tetra mesh", "status": "REVIEW",
                       "note": "At least one mesh contains a non-tetrahedron VTK cell type."})
    else:
        checks.append({"check": "Tetra mesh", "status": "PASS",
                       "note": "All cells were identified as VTK tetrahedron (type 10)."})
    if any(item.get("stress") is None for item in items):
        checks.append({"check": "Stress field", "status": "REVIEW",
                       "note": "One or more inputs lack a compatible PointData stress array."})
    else:
        checks.append({"check": "Stress field", "status": "INFO",
                       "note": "Stress components were extracted; physical meaning depends on their ordering."})
    return checks

def _benchmark_delta(items, cfg):
    bench = cfg.get("beam_theory")
    if not bench:
        return None
    required = ("span_mm", "load_N", "young_modulus_MPa", "width_mm",
                "height_mm", "web_mm", "flange_mm")
    if any(k not in bench for k in required):
        raise AnalysisError("beam_theory must specify " + ", ".join(required))
    span, force, elastic, width, depth, web, flange = (float(bench[k]) for k in required)
    if min(span, force, elastic, width, depth, web, flange) <= 0:
        raise AnalysisError("beam_theory values must be positive.")
    if web >= width or flange*2 >= depth:
        raise AnalysisError("beam_theory H-section dimensions are invalid.")
    inertia = (width*depth**3 - (width-web)*(depth-2*flange)**3)/12
    theoretical_uz = force*span**3/(48*elastic*inertia)
    return {
        "assumptions": "Euler-Bernoulli, simply supported beam, central vertical point load",
        "moment_of_inertia_mm4": inertia,
        "max_vertical_deflection_mm": theoretical_uz,
        "comparisons": [
            {"label": item["label"], "percent_deviation_from_ideal":
             _percent_delta(item["max_abs_vertical_displacement"], theoretical_uz)}
            for item in items
        ],
        "caution": "Idealized theory is not an independent proof of the finite-element result."
    }

def analyze_input(input_file, output_dir, config_path=None):
    """One input resource: .vtu for single analysis, .zip for 1..30 cases."""
    start = time.perf_counter()
    source = Path(input_file)
    dest = Path(output_dir)
    if not source.is_file():
        raise FileNotFoundError("Input result file does not exist: " + source.name)
    dest.mkdir(parents=True, exist_ok=True)
    config = {}
    if config_path:
        config = _load_config(Path(config_path).read_text(encoding="utf-8-sig"))

    cases = []
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            names = [i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".vtu")]
            if not names:
                raise AnalysisError("Archive has no .vtu. Upload a .vtu or ZIP containing .vtu results.")
            if len(names) > MAX_VTU_FILES:
                raise AnalysisError(f"Archive contains {len(names)} VTUs; portable limit is {MAX_VTU_FILES}.")
            if sum(i.file_size for i in names) > MAX_ARCHIVE_BYTES:
                raise AnalysisError("Archive contains too much uncompressed VTU data.")
            internal = [i for i in z.infolist()
                        if not i.is_dir() and i.filename.rsplit("/",1)[-1] == "beam_validation_config.json"]
            if internal and not config_path:
                if internal[0].file_size > 100_000:
                    raise AnalysisError("Embedded validation config file is too large.")
                config = _load_config(z.read(internal[0]).decode("utf-8-sig"))
            for info in sorted(names, key=lambda j: j.filename):
                if info.file_size > MAX_VTU_BYTES:
                    raise AnalysisError(f"VTU archive entry too large: {info.filename}")
                with z.open(info, "r") as f:
                    item = parse_vtu(f, info.filename, config)
                with z.open(info, "r") as f:
                    item["sha256"] = _hash_stream(f)
                item.update(_case_metadata(info.filename, config))
                cases.append(item)
    else:
        if source.suffix.lower() != ".vtu":
            raise AnalysisError("Unsupported input; use a .vtu file or a ZIP containing VTU files.")
        if source.stat().st_size > MAX_VTU_BYTES:
            raise AnalysisError("VTU is above portable size limit.")
        with source.open("rb") as f:
            item = parse_vtu(f, source.name, config)
        with source.open("rb") as f:
            item["sha256"] = _hash_stream(f)
        item.update(_case_metadata(source.name, config))
        cases.append(item)

    def sorting_key(item):
        h = item.get("mesh_size_mm")
        return (-float(h) if h is not None else 1e8,
                item["cells"], item["source"])
    if all(c["mesh_size_mm"] is not None for c in cases):
        cases.sort(key=sorting_key)
    else:
        cases.sort(key=lambda c: (c["cells"], c["source"]))

    metrics = ["points", "cells", "max_displacement_magnitude",
               "max_abs_vertical_displacement", "p95_abs_vertical_displacement"]
    diffs = []
    for a,b in zip(cases,cases[1:]):
        diffs.append({
            "coarse": a["label"], "fine": b["label"],
            "coarse_cells": a["cells"], "fine_cells": b["cells"],
            "max_abs_vertical_delta_percent":
                _percent_delta(a["max_abs_vertical_displacement"],
                               b["max_abs_vertical_displacement"]),
            "stress_component0_abs_delta_percent":
                (_percent_delta(a["stress"]["component_stats"][0]["maximum_absolute"],
                                b["stress"]["component_stats"][0]["maximum_absolute"])
                 if a.get("stress") and b.get("stress") else None),
        })
    warnings = [
        "VTU does not prove the input material, support or total force; review INP and solver log.",
        "Two-mesh displacement agreement is preliminary stability, not proof of grid convergence.",
        "The first StaticStress component is not automatically von Mises.",
        "Stress peaks can be mesh sensitive near concentrated loads and sharp corners."
    ]
    checks = _settings_checks(cases, config)
    limit = float((config.get("validation") or {}).get("displacement_change_limit_percent", 1.0))
    if limit <= 0 or not math.isfinite(limit):
        raise AnalysisError("displacement_change_limit_percent must be positive.")
    if diffs:
        max_delta = max((d["max_abs_vertical_delta_percent"] if d["max_abs_vertical_delta_percent"] is not None else math.inf) for d in diffs)
        checks.append({
            "check": "Displacement mesh sensitivity",
            "status": "PRELIMINARY" if max_delta <= limit else "REVIEW",
            "note": f"Maximum adjacent-mesh difference {max_delta:.4f}% "
                    f"(user-selectable reference limit {limit:.2f}%)."
        })
    else:
        checks.append({
            "check": "Grid convergence",
            "status": "NOT_VERIFIED", "note": "Only one mesh was provided."
        })
    theory = _benchmark_delta(cases, config)
    if theory:
        checks.append({"check": "Ideal beam analytical cross-check", "status": "REFERENCE_ONLY",
                       "note": "Reference formula used only when explicit case metadata was provided."})
    # Test proportionality U ~ load for 2+ cases with the same mesh size.
    linearity = None
    loads = [c.get("load_N") for c in cases]
    if len(cases) >= 3 and all(isinstance(x,(int,float)) and x > 0 for x in loads):
        meshes = [c.get("mesh_size_mm") for c in cases]
        if len({x for x in meshes}) == 1:
            u = [c["max_abs_vertical_displacement"] for c in cases]
            slope = sum(x*y for x,y in zip(loads,u)) / sum(x*x for x in loads)
            predicted = [slope*x for x in loads]
            rms_rel = math.sqrt(sum(((y-yhat)/y)**2 for y,yhat in zip(u,predicted) if y) /
                                max(1, sum(bool(y) for y in u))) * 100
            linearity = {"slope_displacement_per_newton": slope,
                         "rms_relative_deviation_percent": rms_rel,
                         "meaning": "Load proportionality is observed, not proof of true material linearity."}
    result = {
        "tool": "BeamResultVerifier", "version": VERSION,
        "input_file": source.name,
        "num_cases": len(cases),
        "units": config.get("units", {"length":"not_encoded_in_vtu",
                                     "stress":"not_encoded_in_vtu"}),
        "cases": cases,
        "mesh_differences": diffs,
        "checks": checks,
        "ideal_beam_reference": theory,
        "load_proportionality": linearity,
        "warnings": warnings,
        "metadata": {"metric_definitions": {
            "max_displacement_magnitude": "maximum norm of nodal U vector",
            "max_abs_vertical_displacement": "maximum abs of nodal U_z; assumes Z vertical",
            "stress_component0": "first component only; not von Mises unless labeled as such"
        }}
    }
    result["elapsed_seconds"] = round(time.perf_counter()-start,3)
    generate_report(result, dest)
    return dest / REPORT_NAME, result

def _fmt(v, digits=5):
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:,.{digits}f}"
    return str(v)

def _escape(x):
    return html.escape(str(x),quote=True)

def _svg_chart(cases):
    """An original, portable SVG comparison plot (English chart labels)."""
    x0, y0, width, height = 115, 65, 630, 285
    vals = [c["max_abs_vertical_displacement"] for c in cases]
    maxv = max(max(vals)*1.1, 1e-12)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="850" height="420" '
        'viewBox="0 0 850 420" role="img" aria-label="Vertical displacement comparison">',
        '<rect x="0" y="0" width="850" height="420" fill="#ffffff"/>',
        '<text x="35" y="30" font-size="20" font-weight="600" fill="#23415c">Maximum |Uz| by case</text>',
    ]
    for j in range(5):
        value = maxv*j/4
        y = y0+height-j*height/4
        lines.append(f'<path d="M{x0} {y:.1f} H{x0+width}" stroke="#e1e7ef" stroke-width="1"/>')
        lines.append(f'<text x="{x0-12}" y="{y+4:.1f}" font-size="12" text-anchor="end" '
                     f'fill="#576b80">{value:.3g}</text>')
    bar_width = min(90, 490 / max(1,len(cases)))
    for i,c in enumerate(cases):
        x = x0+(i+0.5)*width/len(cases)
        h = (c["max_abs_vertical_displacement"]/maxv)*height
        lines.append(f'<rect x="{x-bar_width/2:.1f}" y="{y0+height-h:.1f}" width="{bar_width:.1f}" '
                     f'height="{max(h,1):.1f}" rx="4" fill="#487da4"/>')
        lines.append(f'<text x="{x:.1f}" y="{y0+height-h-8:.1f}" text-anchor="middle" '
                     f'font-size="12" fill="#26445c">{c["max_abs_vertical_displacement"]:.4f}</text>')
        label = str(c["label"])[:16]
        lines.append(f'<text x="{x:.1f}" y="{y0+height+24:.1f}" text-anchor="middle" '
                     f'font-size="11" fill="#475c71">{_escape(label)}</text>')
    lines.append(f'<text x="{x0+width/2}" y="408" text-anchor="middle" font-size="12" '
                 f'fill="#576b80">Case / mesh resolution</text>')
    lines.append('</svg>')
    return "\n".join(lines)

def generate_report(result, output_dir):
    """Create stable, inspectable outputs then ZIP them for the platform."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/"validation.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False), encoding="utf-8"
    )
    with (output_dir/"metrics.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f)
        w.writerow(["Case","Source","Mesh size (mm)","Points","Cells",
                    "Max displacement magnitude","Max |Uz|",
                    "Min Uz","Max Uz","P95 |Uz|","Stress comp0 abs peak",
                    "Input SHA-256"])
        for c in result["cases"]:
            ss = (c.get("stress") or {}).get("component_stats", [])
            w.writerow([c["label"],c["source"],c.get("mesh_size_mm"),
                        c["points"], c["cells"],
                        c["max_displacement_magnitude"], c["max_abs_vertical_displacement"],
                        c["minimum_vertical_displacement"], c["maximum_vertical_displacement"],
                        c["p95_abs_vertical_displacement"],
                        ss[0]["maximum_absolute"] if ss else "",
                        c["sha256"]])
    with (output_dir/"comparison.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f)
        w.writerow(["Coarse case","Fine case","Coarse cells","Fine cells",
                    "Max |Uz| change (%)","Stress comp0 peak change (%)"])
        for d in result["mesh_differences"]:
            w.writerow([d["coarse"],d["fine"],d["coarse_cells"],d["fine_cells"],
                        d["max_abs_vertical_delta_percent"],
                        d["stress_component0_abs_delta_percent"]])
    (output_dir/"displacement_chart.svg").write_text(
        _svg_chart(result["cases"]),encoding="utf-8"
    )
    th = '<tr><th>Case</th><th>Nodes</th><th>Elements</th><th>Max |U|</th><th>Max |Uz|</th><th>P95 |Uz|</th></tr>'
    rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            _escape(c["label"]),_fmt(c["points"]),_fmt(c["cells"]),
            _fmt(c["max_displacement_magnitude"],4),
            _fmt(c["max_abs_vertical_displacement"],4),
            _fmt(c["p95_abs_vertical_displacement"],4))
        for c in result["cases"]
    )
    diff_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}%</td><td>{}%</td></tr>".format(
            _escape(d["coarse"]),_escape(d["fine"]),
            _fmt(d["max_abs_vertical_delta_percent"],4),
            _fmt(d["stress_component0_abs_delta_percent"],3))
        for d in result["mesh_differences"]
    )
    check_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            _escape(c["check"]),_escape(c["status"]),_escape(c["note"]))
        for c in result["checks"]
    )
    stress_rows = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            _escape(c["label"]),
            _escape((c.get("stress") or {}).get("array") or "missing"),
            _fmt((c.get("stress") or {}).get("component_stats", [{}])[0].get("maximum_absolute")),
            _fmt((c.get("stress") or {}).get("mises_from_explicit_voigt_order")
                 or (c.get("mises_scalar") or {}).get("maximum"))
        ) for c in result["cases"]
    )
    linear = result.get("load_proportionality")
    linearity_note = (
        "<p>已根据明确标注的载荷数值计算线性比例拟合。"
        f"相对均方根偏差：{_fmt(linear['rms_relative_deviation_percent'],3)}%。"
        "这只是结果对载荷的比例关系，不证明材料参数或支座设置正确。</p>"
        if linear else "<p>未检测到至少三个同网格、不同载荷的明确工况，跳过载荷比例拟合。</p>"
    )
    theory_note = "<p>未提供完整 beam_theory 参数，因此不自动推断几何尺寸、载荷和材料。</p>"
    theory = result.get("ideal_beam_reference")
    if theory:
        theory_comparison = "; ".join(
            "{}: deviation {}%".format(_escape(t["label"]),
                                       _fmt(t["percent_deviation_from_ideal"],3))
            for t in theory["comparisons"]
        )
        theory_note = (
            "<p>基于明确给定的理想简支梁参数，Euler–Bernoulli 理论挠度：<b>{} mm</b>。"
            "各工况与该参考值的差异：{}。这一参考值依赖给定假设，不能替代真实求解校验。</p>"
        ).format(_fmt(theory["max_vertical_deflection_mm"],4),
                 theory_comparison)
    comparisons = (
        "<table><thead><tr><th>Coarse</th><th>Fine</th>"
        "<th>Δ max |Uz|</th><th>Δ stress component 0</th></tr></thead>"
        "<tbody>"+diff_rows+"</tbody></table>"
        if diff_rows else "<p>单文件模式：没有第二个网格，无法进行网格差异比较。</p>"
    )
    warning_items = "".join("<li>{}</li>".format(_escape(w)) for w in result["warnings"])
    doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BeamResultVerifier v{VERSION} | Validation Report</title>
<style>
*{{box-sizing:border-box}}body{{background:#f4f7fa;color:#263d52;margin:0;
font:15px/1.7 "Microsoft YaHei",Arial,sans-serif}}
main{{max-width:1040px;margin:30px auto;background:white;padding:40px 48px;
border:1px solid #dfe7ec;border-radius:12px}}
h1{{font-size:26px;margin:4px 0 8px}}h2{{font-size:18px;margin:30px 0 12px;
padding-bottom:8px;border-bottom:1px solid #e0e8ed}}
small,.muted{{color:#5c7181}}.eyebrow{{font-size:12px;letter-spacing:.1em;
font-weight:700;color:#527991}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;margin:24px 0}}
.kpis div{{border:1px solid #dbe5eb;border-radius:8px;padding:14px 17px;min-width:190px}}
.kpis b{{display:block;font-size:23px;color:#245d79}}
table{{border-collapse:collapse;width:100%;font-size:13px;overflow:hidden}}
th,td{{padding:10px 12px;border-bottom:1px solid #e1e8ee;text-align:left;vertical-align:top}}
th{{background:#f0f5f8}}.scroll{{overflow-x:auto}}
.warning{{border-left:3px solid #d6a151;background:#fffaf0;padding:10px 16px}}
.warning li{{padding:2px 0}}
.chart{{width:100%;border:1px solid #edf2f4;border-radius:8px}}
@media print{{body{{background:white}}main{{border:0;margin:0;padding:10px}}}}
</style></head><body><main>
<div class="eyebrow">OPENCAE / BEAM VERIFICATION MODULE · V{VERSION}</div>
<h1>钢梁 VTU 自动验证报告</h1>
<p class="muted">输入：{_escape(result["input_file"])} · 算例数量：{result["num_cases"]} ·
执行耗时：{result["elapsed_seconds"]:.3f} 秒</p>
<div class="kpis">
<div><small>Number of cases</small><b>{result["num_cases"]}</b></div>
<div><small>Max |Uz| / first case</small>
<b>{result["cases"][0]["max_abs_vertical_displacement"]:.4f}</b></div>
<div><small>Data checks</small><b>{len(result["checks"])}</b></div>
</div>
<h2>Displacement overview</h2>
<img class="chart" src="displacement_chart.svg" alt="Maximum vertical displacement by mesh"/>
<p class="muted">Chart values use original result units. VTU does not guarantee mm unless separately documented.</p>
<h2>数值汇总</h2><div class="scroll"><table><thead>{th}</thead><tbody>{rows}</tbody></table></div>
<h2>网格敏感性</h2><div class="scroll">{comparisons}</div>
<p class="muted">两组网格的位移变化较小，只能说明该指标具有初步稳定性，不能单凭此证明全部应力收敛。</p>
<h2>应力字段摘要</h2><div class="scroll"><table>
<thead><tr><th>Case</th><th>Stress field</th><th>Component 0 abs peak</th><th>Mises (only if reliable)</th></tr></thead>
<tbody>{stress_rows}</tbody></table></div>
<p class="muted">未经明确分量顺序证明，第一应力分量不是 von Mises。空白表示未进行该换算。</p>
<h2>载荷比例关系（可选）</h2>{linearity_note}
<h2>自动检查结果</h2><div class="scroll"><table>
<thead><tr><th>Check</th><th>Status</th><th>Meaning</th></tr></thead>
<tbody>{check_rows}</tbody></table></div>
<h2>理论参照（可选）</h2>{theory_note}
<h2>验证边界与后续建议</h2><div class="warning"><ul>{warning_items}</ul></div>
<p class="muted">数据来源为既有求解结果；本程序不重新求解。完整原始数据、SHA-256、
网格差异和各项检查状态见 validation.json、metrics.csv 和 comparison.csv。</p>
</main></body></html>"""
    (output_dir/"analysis_report.html").write_text(doc,encoding="utf-8")
    (output_dir/"HOW_TO_READ.txt").write_text(
        "1. Extract entire report ZIP to one folder.\n"
        "2. Open analysis_report.html in a web browser (keep SVG alongside).\n"
        "3. Check validation.json for raw metric values and cautions.\n"
        "4. VTU analysis cannot prove solver correctness, load, material or safety.\n",
        encoding="utf-8"
    )
    targets = ["analysis_report.html","displacement_chart.svg","metrics.csv",
               "comparison.csv","validation.json","HOW_TO_READ.txt"]
    final = output_dir/REPORT_NAME
    with zipfile.ZipFile(final,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for name in targets:
            z.write(output_dir/name,name)
    if not final.exists() or final.stat().st_size == 0:
        raise OSError("Report ZIP was not created correctly.")
    return final

def main(argv=None):
    p=argparse.ArgumentParser(description="Analyze one VTU or multiple VTUs in ZIP")
    p.add_argument("--input",required=True,help="single .vtu OR a .zip containing VTUs")
    p.add_argument("--output-dir",default="beam_report")
    p.add_argument("--config",default=None,
                   help="optional JSON settings for units, beam theory and case labels")
    args=p.parse_args(argv)
    out,result=analyze_input(args.input,args.output_dir,args.config)
    print("[SUCCESS] Cases:",result["num_cases"])
    print("[SUCCESS] Report:",out)
    for c in result["cases"]:
        print("[METRIC]",c["label"],"Max |Uz| =",round(c["max_abs_vertical_displacement"],6))

if __name__=="__main__":
    main()
