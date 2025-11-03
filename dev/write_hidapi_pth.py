#!/usr/bin/env python3
"""
Write a .pth into site-packages that adds the local hidapi bin dir
to the DLL search path on Windows via os.add_dll_directory.

Usage (optional): write_hidapi_pth.py <repo_dir> <env_sitepackages_dir>
"""

from __future__ import annotations
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if sys.platform != "win32":
        # No-op outside Windows.
        return 0

    if len(argv) >= 3:
        repo_dir = Path(argv[1]).resolve()
        site_packages = Path(argv[2]).resolve()
    else:
        repo_dir = Path.cwd()
        site_packages = Path(sys.prefix, "Lib", "site-packages")

    dll_dir = repo_dir / "build" / "local-hidapi" / "windows" / "bin"
    if not dll_dir.is_dir():
        print(f"[hidapi .pth] skip: {dll_dir} does not exist", file=sys.stderr)
        return 0

    site_packages.mkdir(parents=True, exist_ok=True)
    pth_path = site_packages / "plover_hidapi_add_dll_dir.pth"

    # Keep it one line: .pth executes arbitrary Python on import.
    # Include defensive checks for directory existence and DLL loading
    code = (
        "import os,sys;"
        "p=r%r;"
        "os.add_dll_directory(p) if sys.platform=='win32' and hasattr(os,'add_dll_directory') and os.path.isdir(p) else None\n"
        % (str(dll_dir),)
    )

    try:
        pth_path.write_text(code, encoding="utf-8")
        print(f"[hidapi .pth] wrote {pth_path}")
        return 0
    except Exception as e:
        print(f"[hidapi .pth] failed to write {pth_path}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
