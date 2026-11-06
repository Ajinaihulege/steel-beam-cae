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



def _recursive_unique(root: Path, path_hint: str):
    """Search one controlled root. Relative directory hints must match suffix."""
    if not root.is_dir():
        return None
    normalized = path_hint.replace("\\", "/").strip("/")
    basename = normalized.rsplit("/", 1)[-1]
    if not basename or Path(basename).suffix.lower() not in VALID_SUFFIXES:
        return None
    hits = []
    try:
        for candidate in root.rglob(basename):
            checked = _existing_file(candidate)
            if checked is None:
                continue
            try:
                relative = checked.relative_to(root.resolve()).as_posix()
            except ValueError:
                # Ignore a symlink escaping the allowed search root.
                continue
            if "/" in normalized and not (
                relative.casefold() == normalized.casefold() or
                relative.casefold().endswith("/" + normalized.casefold())
            ):
                continue
            hits.append(checked)
            if len(hits) > 1:
                raise InputResolutionError(
                    "Ambiguous resource path: multiple matching VTU/ZIP files under "
                    f"'{root}'. Provide an explicit full path or complete relative path."
                )
    except InputResolutionError:
        raise
    except (OSError, PermissionError):
        return None
    return hits[0] if hits else None


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
    - When a basename is supplied and a project ID exists, searches only
      that project's cached inputs; ambiguous matches are rejected.
    - Without a project ID, searches temp only if the basename is unique.
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
            override_path = Path(override).expanduser()
            if not override_path.is_absolute():
                raise InputResolutionError(
                    "BEAM_VERIFIER_INPUT_FILE must be an explicit absolute path."
                )
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

        if not candidate.is_absolute() and candidate.name and main:
            # Prefer only paths tied to this project. A shared temp folder may
            # contain another team's same-named VTU and is not safe to guess.
            project_id = ctx.get("sys_project_id")
            if project_id is not None:
                scoped_roots = [main / "temp" / str(project_id)]
                local_root = main / "Local"
                if local_root.is_dir():
                    scoped_roots += [
                        user / f"project-{project_id}"
                        for user in local_root.glob("User-*") if user.is_dir()
                    ]
                matches = []
                for search_root in scoped_roots:
                    result = _recursive_unique(search_root, raw)
                    if result is not None:
                        matches.append(result)
                        if len(matches) > 1:
                            raise InputResolutionError(
                                "Ambiguous resource: more than one matching "
                                "VTU/ZIP in current project caches."
                            )
                if matches:
                    return matches[0]
            else:
                # No project ID is known: only an explicitly named file may
                # be matched if unique in the local temp search scope.
                found = _recursive_unique(main / "temp", raw)
                if found:
                    return found

    raise InputResolutionError(
        "Input resource was named, but the VTU/ZIP file could not be read. "
        f"Received path hint(s): {hints!r}. "
        "Check resource download and the CFF APIParameterTemlate mapping."
    )
