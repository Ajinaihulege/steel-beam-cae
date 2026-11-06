# -*- coding: utf-8 -*-
"""Build the plugin registration package from the source tree.

Usage: python build_plugin.py
Result: dist/<Name>-<version>-REGISTER.zip
"""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
PLUGIN_FILES = [
    "PluginConfig.xml", "beam_analyzer.py", "beam_verifier_adapter.py",
    "input_resolver.py", "requirements.txt", "example_beam_config.json",
    "README.md", "CHANGELOG.md"
]


def build():
    cfg = ET.parse(ROOT / "PluginConfig.xml").getroot()
    version = cfg.findtext("version")
    plugin_name = cfg.findtext("Name")
    info = cfg.find(".//ApiInfo")
    app = cfg.find(".//AppInfo")
    if cfg.tag != "PluginConfig" or not version or not plugin_name:
        raise ValueError("Invalid PluginConfig.xml root/Name/version.")
    if info is None or app is None:
        raise ValueError("PluginConfig.xml requires ApiInfo and AppInfo.")
    if info.get("AppPath") != app.get("AppPath"):
        raise ValueError("ApiInfo.AppPath must match AppInfo.AppPath.")
    if info.get("AppType") != "PythonAdapter" or info.get("HasUI") != "false":
        raise ValueError("Unexpected AppType/HasUI for this headless plugin.")
    if info.get("APIName") != "BeamResultVerifierCommonTest":
        raise ValueError("Current test CFF API mapping has changed.")
    if info.get("APIParameterTemlate") != "filepath=%filepath%":
        raise ValueError("Input mapping has changed; revalidate against platform manual.")

    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    output = output_dir / f"{plugin_name}-{version}-REGISTER.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for rel in PLUGIN_FILES:
            path = ROOT / rel
            if not path.is_file():
                raise FileNotFoundError("Missing plugin source: " + rel)
            entry = ZipInfo(rel, date_time=(2026, 11, 6, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = (0o644 << 16)
            archive.writestr(entry, path.read_bytes())
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP checksum verification failed.")
        if archive.namelist()[0] != "PluginConfig.xml":
            raise RuntimeError("PluginConfig.xml must be at archive root.")
    print("Created:",output)
    return output


if __name__ == "__main__":
    build()
