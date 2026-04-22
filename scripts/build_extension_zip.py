from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from common import abs_path


SKIP_DIRS = {"__pycache__", ".DS_Store"}
SKIP_SUFFIXES = (".test.js", ".spec.js")


def should_package(path: Path, extension_dir: Path) -> bool:
    if path.name in SKIP_DIRS:
        return False
    if any(part in SKIP_DIRS for part in path.relative_to(extension_dir).parts):
        return False
    if path.suffix.lower() in {".md"}:
        return False
    return not any(path.name.endswith(suffix) for suffix in SKIP_SUFFIXES)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Chrome extension ZIP archive.")
    parser.add_argument("--extension-dir", required=True, help="Extension source directory.")
    parser.add_argument("--out", required=True, help="ZIP output path.")
    args = parser.parse_args()

    extension_dir = abs_path(args.extension_dir)
    out_path = abs_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(extension_dir.rglob("*")):
            if path.is_file() and should_package(path, extension_dir):
                archive.write(path, path.relative_to(extension_dir))

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
