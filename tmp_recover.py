"""Recover emptied .py modules from their __pycache__ .pyc bytecode.

Usage: python tmp_recover.py [--dry-run]
Recovers each module by decompiling its compiled bytecode with decompyle3.
"""

from __future__ import annotations

import glob
import os
import sys

from io import StringIO


def load_code_object(pyc_path: str):
    """Load the code object from a .pyc using xdis (bundled with decompyle3)."""
    from xdis import load_module

    version, timestamp, magic_int, co, is_pypy, source_size, sip_hash = load_module(
        pyc_path
    )
    return version, co


def decompile_pyc(pyc_path: str) -> str:
    """Decompile a .pyc file to source text."""
    import decompyle3.main as dm

    version, co = load_code_object(pyc_path)
    out = StringIO()
    dm.decompile(co, version, out)
    return out.getvalue()


def recover(pyc_path: str, py_path: str, dry_run: bool = False) -> bool:
    """Decompile pyc_path -> write py_path. Return True on success."""
    try:
        source = decompile_pyc(pyc_path)
    except Exception as exc:  # noqa: BLE001
        print(f"  [!] FAILED {os.path.basename(pyc_path)}: {exc}")
        return False
    if dry_run:
        print(f"  [dry] {os.path.basename(pyc_path)} -> {len(source)} bytes")
        return True
    with open(py_path, "w", encoding="utf-8") as fh:
        fh.write(source)
    print(f"  [ok] {os.path.basename(pyc_path)} -> {py_path} ({len(source)} bytes)")
    return True


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args

    all_pyc = glob.glob(os.path.join("src", "friday", "server", "__pycache__", "*.pyc"))
    all_pyc += glob.glob(
        os.path.join("src", "friday", "agents", "cortex", "__pycache__", "*.pyc")
    )
    seen: set[str] = set()
    unique: list[str] = []
    for p in all_pyc:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    ok = 0
    fail = 0
    for pyc in unique:
        base = os.path.basename(pyc)
        mod = base.split(".")[0]
        if "cortex" in pyc:
            py_path = os.path.join("src", "friday", "agents", "cortex", mod + ".py")
        else:
            py_path = os.path.join("src", "friday", "server", mod + ".py")
        if recover(pyc, py_path, dry_run=dry_run):
            ok += 1
        else:
            fail += 1

    print(f"DONE: ok={ok} fail={fail} dry_run={dry_run}")


if __name__ == "__main__":
    main()
