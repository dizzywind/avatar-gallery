#!/usr/bin/env python3
"""
Validator for Avatar Gallery data.json entries.

Checks:
- prompt: non-empty string
- theme: one of allowed themes
- seed: positive integer (when present)
- id: non-empty string, no spaces
- Unknown fields flagged as warnings
- filename: non-empty string (for legacy entries without seed)
- fileSize: positive integer (when present)

Usage:
  python3 validator.py [path/to/data.json]
"""

import json
import os
import sys
from pathlib import Path

ALLOWED_THEMES = {
    "lotus", "fantasy", "scifi", "sci-fi", "nature", "abstract",
    "mythology", "tattoo", "watercolor", "minimalist", "minimal",
    "uncategorized", "portrait", "animals", "retro",
}

VALID_LEGACY_FIELDS = {
    "id", "filename", "prompt", "theme", "category",
    "createdAt", "width", "height", "fileSize",
}

VALID_NEW_FIELDS = {
    "id", "prompt", "theme", "category", "createdAt", "seed",
}

ALL_VALID_FIELDS = VALID_LEGACY_FIELDS | VALID_NEW_FIELDS


def validate(data_path: str) -> int:
    path = Path(os.path.expanduser(data_path))

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return 1
    if not path.is_file():
        print(f"ERROR: Not a regular file: {path}")
        return 1

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON at position {e.pos}: {e.msg}")
        return 1

    issues_found = False

    # Top-level structure
    if "avatars" not in data:
        print("ERROR: Missing 'avatars' list at root")
        return 1

    avatars = data["avatars"]
    if not isinstance(avatars, list):
        print("ERROR: 'avatars' is not a list")
        return 1

    total = len(avatars)
    print(f"Validating {total} avatar entries...")

    warn_ids = set()
    errors = []
    warnings = []

    for i, avatar in enumerate(avatars):
        prefix = f"[{i}] id={avatar.get('id', 'MISSING')}"

        if not isinstance(avatar, dict):
            errors.append(f"{prefix}: Entry is not a dict")
            continue

        # --- Required: id ---
        entry_id = avatar.get("id")
        if not isinstance(entry_id, str) or not entry_id.strip():
            errors.append(f"{prefix}: 'id' must be non-empty string")
        elif " " in entry_id:
            errors.append(f"{prefix}: 'id' contains spaces: {entry_id!r}")
        elif entry_id in warn_ids:
            errors.append(f"{prefix}: Duplicate id: {entry_id}")
        warn_ids.add(entry_id)

        # --- Required: prompt ---
        prompt = avatar.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{prefix}: 'prompt' must be non-empty string")

        # --- Required: theme ---
        theme = avatar.get("theme")
        if not isinstance(theme, str) or theme not in ALLOWED_THEMES:
            # Allow "sci-fi" as alias for "scifi"
            normalized = theme.replace("sci-fi", "scifi").replace("minimal", "minimalist") if isinstance(theme, str) else theme
            if normalized not in ALLOWED_THEMES:
                errors.append(f"{prefix}: 'theme' must be one of {sorted(ALLOWED_THEMES)}, got {theme!r}")

        # --- Optional: seed ---
        seed = avatar.get("seed")
        if seed is not None:
            if not isinstance(seed, int) or seed <= 0:
                errors.append(f"{prefix}: 'seed' must be positive integer, got {seed!r}")

        # --- Legacy: filename ---
        has_seed = seed is not None
        filename = avatar.get("filename")
        if not has_seed:
            if not isinstance(filename, str) or not filename.strip():
                errors.append(f"{prefix}: Legacy entry without 'seed' must have 'filename'")

        # --- Legacy: fileSize ---
        file_size = avatar.get("fileSize")
        if file_size is not None:
            if not isinstance(file_size, int) or file_size <= 0:
                errors.append(f"{prefix}: 'fileSize' must be positive integer, got {file_size!r}")

        # --- Unknown fields ---
        for key in avatar:
            if key not in ALL_VALID_FIELDS:
                warnings.append(f"{prefix}: Unknown field '{key}'")

    # Check _meta consistency
    meta = data.get("_meta", {})
    computed_total = len(avatars)
    reported_total = meta.get("totalImages")
    if reported_total is not None and isinstance(reported_total, int) and reported_total != computed_total:
        warnings.append(f"_meta.totalImages={reported_total} but actual avatar count={computed_total}")

    metadata = data.get("metadata", {})
    reported_meta_total = metadata.get("total")
    if reported_meta_total is not None and isinstance(reported_meta_total, int) and reported_meta_total != computed_total:
        warnings.append(f"metadata.total={reported_meta_total} but actual avatar count={computed_total}")

    # Report
    print()
    if errors:
        issues_found = True
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")

    if not issues_found and not warnings:
        print("✓ All checks passed — data.json is valid")

    print(f"\nSummary: {total} entries, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if issues_found else 0


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "/root/avatar-gallery/data.json"
    sys.exit(validate(path_arg))
