# -*- coding: utf-8 -*-
"""Build a root-level PluginConfig.xml ZIP from this repository.

Usage: python build_plugin.py
Output: dist/BeamResultVerifierCommonTest-3.0.2.0-REGISTER.zip
"""
from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
FILES = [
    "PluginConfig.xml", "beam_analyzer.py", "beam_verifier_adapter.py",
    "input_resolver.py", "requirements.txt", "example_beam_config.json",
    "README.md", "CHANGELOG.md"
]


def build():
    config = ET.parse(ROOT / "PluginConfig.xml").getroot()
    version = config.findtext("version")
    plugin_name = config.findtext("Name")
    if not version or not plugin_name:
        raise ValueError("PluginConfig.xml is missing version or Name.")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    output = dist / f"{plugin_name}-{version}-REGISTER.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name in FILES:
            source = ROOT / name
            if not source.is_file():
                raise FileNotFoundError(str(source))
            info = ZipInfo(name, date_time=(2026, 11, 5, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    with ZipFile(output) as archive:
        assert "PluginConfig.xml" in archive.namelist()
        assert not archive.testzip()
    print("Created:", output)
    return output


if __name__ == "__main__":
    build()
