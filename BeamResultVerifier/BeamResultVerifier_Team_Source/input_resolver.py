# -*- coding: utf-8 -*-
"""Resolve a concrete VTU/ZIP file passed by OpenCAEHub without guessing cases.

The OpenCAEHub input must contain a usable filename/path or the operator must
explicitly set BEAM_VERIFIER_INPUT_FILE for a controlled diagnostic run.
Never silently pick a 10mm or 15mm beam case when the context filepath is "".
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping


class InputResolutionError(FileNotFoundError):
    """No unambiguous, readable VTU/ZIP resource could be resolved."""


VALID_SUFFIXES = {".vtu", ".zip"}


def _hints(value: Any):
    """Unwrap nested platform values, including Resource slot objects."""
    if isinstance(value, (str, os.PathLike)):
        raw = str(value).strip().strip('"').strip("'")
        if raw and raw.lower().endswith((".vtu", ".zip")):
            yield raw
    elif isinstance(value, dict):
        # Prioritize explicit paths over display names.
        for key in ("filepath", "filePath", "localPath", "path", "uri", "value", "slot"):
            if key in value:
                yield from _hints(value[key])
        name = value.get("name")
        if isinstance(name, str):
            yield from _hints(name)
        # Also support a nested inputParam object without treating UUIDs as paths.
        for key in ("inputParam", "inParam", "input"):
            if key in value:
                yield from _hints(value[key])
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _hints(item)


def _existing_file(path: Path):
    try:
        return path.resolve(strict=True) if path.is_file() and path.suffix.lower() in VALID_SUFFIXES else None
    except (OSError, RuntimeError):
        return None


def _recursive_unique(root: Path, basename: str):
    if not root.is_dir():
        return None
    found = []
    try:
        for candidate in root.rglob(basename):
            checked = _existing_file(candidate)
            if checked is not None:
                found.append(checked)
                if len(found) > 1:
                    raise InputResolutionError(
                        f"Multiple files named '{basename}' exist under '{root}'. "
                        "Provide an explicit full path; do not guess between mesh cases."
                    )
    except InputResolutionError:
        raise
    except (OSError, PermissionError):
        return None
    return found[0] if found else None


def resolve_input_file(
    value: Any,
    context: Mapping[str, Any] | None = None,
    work_dir: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Return a validated local file. Never select a file solely from an empty input.

    - Accepts path string, nested inputParam/filepath, and Resource slot name.
    - Handles absolute paths and paths relative to task work dir / Client / temp.
    - When a basename is supplied, searches temp, then the current project's Local
      cache; multiple matches in one scope require an explicit full path.
    - BEAM_VERIFIER_INPUT_FILE is a *developer-controlled* opt-in fallback only
      when the platform delivered no file hint at all.
    """
    ctx = dict(context or {})
    environ = os.environ if env is None else env
    main = Path(str(ctx.get("sys_main_dir") or "")).expanduser() if ctx.get("sys_main_dir") else None
    work = Path(work_dir).expanduser() if work_dir else None

    hints = list(dict.fromkeys(_hints(value)))
    if not hints:
        for key in ("inParam", "input", "filepath"):
            hints = list(dict.fromkeys(_hints(ctx.get(key))))
            if hints:
                break

    if not hints:
        override = str(environ.get("BEAM_VERIFIER_INPUT_FILE") or "").strip()
        if override:
            hints = [override]
        else:
            raise InputResolutionError(
                "Platform passed an empty input: inParam.inputParam.filepath = ''. "
                "The selected VTU may exist in Client/Local or Client/temp, but "
                "the plugin did NOT receive its filename or path. "
                "Fix the CFF resource-to-PythonAdapter parameter mapping; for a "
                "controlled local diagnostic set BEAM_VERIFIER_INPUT_FILE to the "
                "explicit full path of the intended VTU/ZIP. "
                "No mesh case will be chosen automatically."
            )

    for raw in hints:
        candidate = Path(raw).expanduser()
        bases = [None, work, (main / "temp") if main else None, main]
        for parent in bases:
            p = candidate if parent is None or candidate.is_absolute() else parent / candidate
            found = _existing_file(p)
            if found is not None:
                return found

        if not candidate.is_absolute() and candidate.name:
            # Do not search whole disks or another project.
            if main:
                found = _recursive_unique(main / "temp", candidate.name)
                if found:
                    return found
                project_id = ctx.get("sys_project_id")
                if project_id is not None:
                    for user_dir in (main / "Local").glob("User-*") if (main / "Local").is_dir() else ():
                        root = user_dir / f"project-{project_id}"
                        found = _recursive_unique(root, candidate.name)
                        if found:
                            return found

    raise InputResolutionError(
        "Input resource was named, but the VTU/ZIP file could not be read. "
        f"Received path hint(s): {hints!r}. "
        "Check resource download and the CFF APIParameterTemlate mapping."
    )
