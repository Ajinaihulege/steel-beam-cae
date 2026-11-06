# -*- coding: utf-8 -*-
"""Read-only diagnostics for one OpenCAEHub PythonAdapter run.

Usage:
  python tools/diagnose_context.py "C:/example/38_1464901257_context.json"

Does not access the platform API, edit project data, or rerun any plugin.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def inspect_context_file(path: str | Path, plugin_xml: str | Path | None = None) -> list[str]:
    context_path = Path(path)
    ctx = json.loads(context_path.read_text(encoding="utf-8-sig"))
    if not isinstance(ctx, dict):
        raise ValueError("Context JSON must be an object.")
    messages = [f"Context: {context_path.name}"]
    input_params = ctx.get("inParam") or {}
    if not isinstance(input_params, dict):
        input_params = {}
    named = input_params.get("inputParam") or {}
    if not isinstance(named, dict):
        named = {}
    value = named.get("filepath", input_params.get("filepath", None))
    if value is None or (isinstance(value, str) and not value.strip()):
        messages.append("[FAIL] INPUT EMPTY: PythonAdapter received no filepath.")
        messages.append("Action: check platform Resource -> APIParameterTemlate expansion.")
    else:
        summary = "<structured resource value>" if isinstance(value, dict) else repr(value)
        messages.append("[INFO] Input filepath value: " + summary)
    messages.append("[INFO] logic_command: " + str(ctx.get("logic_command", "<missing>")))

    plugin_dir = str(ctx.get("sys_plugin_dir") or "").replace("\\", "/").rstrip("/")
    expected_name = None
    if plugin_xml:
        config = ET.parse(plugin_xml).getroot()
        expected_name = config.findtext("Name")
        expected_module = config.find(".//ApiInfo")
        if expected_module is not None:
            messages.append("[INFO] Expected APIName: " + str(expected_module.get("APIName")))
    if expected_name:
        if plugin_dir.casefold().endswith("/" + expected_name.casefold()):
            messages.append("[PASS] Runtime plugin directory matches package Name.")
        else:
            messages.append("[WARN] Runtime plugin directory differs from expected "
                            + expected_name + ". Check timestamps and plugin selection.")
    messages.append("[INFO] Runtime plugin: " + (Path(plugin_dir).name if plugin_dir else "<missing>"))

    result_file = Path(ctx.get("sys_result_file") or context_path.with_name(
        context_path.name.replace("_context.json","_result.json")
    ))
    if result_file.is_file():
        try:
            result = json.loads(result_file.read_text(encoding="utf-8-sig"))
            status = result.get("status", "<missing>")
            messages.append("[RESULT] status: " + str(status))
            if result.get("error"):
                messages.append("[RESULT] error: " + str(result["error"]))
        except (ValueError, OSError, AttributeError) as exc:
            messages.append("[WARN] Could not parse result.json: " + str(exc))
    else:
        messages.append("[WARN] No result.json found; task may not have reached adapter.")
    outputs = ctx.get("outParam") or {}
    if isinstance(outputs, dict):
        out_group = outputs.get("outputParam", outputs)
        if isinstance(out_group, dict):
            dest = out_group.get("filepath")
            if isinstance(dest,str) and dest:
                target = Path(dest)
                if target.is_file():
                    delta = target.stat().st_mtime - result_file.stat().st_mtime if result_file.exists() else 0
                    messages.append("[INFO] Report ZIP exists; size: "
                                    + str(target.stat().st_size) + " bytes.")
                    if delta < -2:
                        messages.append("[WARN] Report ZIP predates result.json. "
                                        "It may be left over from a previous run.")
                else:
                    messages.append("[INFO] Expected report ZIP does not exist at output filepath.")
    return messages


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("context",help="existing *_context.json file")
    parser.add_argument("--plugin-xml",default=None,
                        help="optional PluginConfig.xml from the source bundle")
    args = parser.parse_args(argv)
    try:
        messages=inspect_context_file(args.context,args.plugin_xml)
    except (OSError, ValueError, ET.ParseError) as exc:
        parser.exit(2,"Diagnostic could not read context: "+str(exc)+"\n")
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
