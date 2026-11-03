# -*- coding: utf-8 -*-
"""Create a platform uploadable ZIP after confirming registered API identity."""
import argparse
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

def main():
    ap = argparse.ArgumentParser(description="Build BeamResultVerifier plugin ZIP")
    ap.add_argument("--module", required=True, help="Exact registered ModuleFullName")
    ap.add_argument("--api", required=True, help="Exact registered APIName")
    opts = ap.parse_args()
    if not opts.module.strip() or not opts.api.strip():
        raise SystemExit("Missing module/API identity")
    d = Path(__file__).resolve().parent
    tpl = (d / "PluginConfig.xml.template").read_text(encoding="utf-8")
    xml = tpl.replace("__MODULE_FULL_NAME__", escape(opts.module.strip(), {'"':'&quot;'}))
    xml = xml.replace("__API_NAME__", escape(opts.api.strip(), {'"':'&quot;'}))
    ET.fromstring(xml)  # Validate before packaging
    dest = d / "BeamResultVerifier-1.0.0.1.zip"
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("PluginConfig.xml", xml)
        for f in ("beam_analyzer.py", "beam_verifier_adapter.py", "requirements.txt", "README.md"):
            z.write(d / f, f)
    print("Created:", dest)
    print("Check target platform API identity before installing.")

if __name__ == "__main__":
    main()
