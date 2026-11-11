"""Path-locked, read-only filesystem view.

A tiny sandbox: every requested path is resolved against a fixed root and
must stay inside it. Both ``..`` traversal and symlink escapes that leave
the root are rejected. Standard library only, no network access.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_MAX_BYTES = 1_000_000  # 1 MB read cap


class SandboxError(ValueError):
    """Raised when a path is outside the root or otherwise unreadable."""


def resolve(root: str | os.PathLike, requested: str | os.PathLike) -> Path:
    """Resolve *requested* against *root*.

    Returns the absolute, symlink-resolved path. Raises :class:`SandboxError`
    if the resolved path escapes the (also resolved) root.
    """
    root_path = Path(root).resolve()
    # Reject absolute requests outright: everything is relative to the root.
    req = Path(requested)
    if req.is_absolute():
        raise SandboxError(f"absolute paths are not allowed: {requested!r}")
    candidate = (root_path / req).resolve()
    if candidate != root_path and root_path not in candidate.parents:
        raise SandboxError(f"path escapes the sandbox root: {requested!r}")
    return candidate


def list_resources(root: str | os.PathLike) -> list[str]:
    """List files under *root* as POSIX-style relative paths, sorted.

    Hidden files and directories (names starting with ``.``) are skipped.
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise SandboxError(f"root is not a directory: {root!r}")
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune hidden directories in place so os.walk never descends into them.
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            full = Path(dirpath) / name
            found.append(full.relative_to(root_path).as_posix())
    return sorted(found)


def read_resource(
    root: str | os.PathLike,
    requested: str | os.PathLike,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> str:
    """Read a file inside *root* as text.

    Raises :class:`SandboxError` for escapes, missing files, directories,
    and files larger than *max_bytes*.
    """
    path = resolve(root, requested)
    if not path.exists():
        raise SandboxError(f"no such file: {requested!r}")
    if not path.is_file():
        raise SandboxError(f"not a file: {requested!r}")
    if path.stat().st_size > max_bytes:
        raise SandboxError(
            f"file exceeds size cap ({max_bytes} bytes): {requested!r}"
        )
    return path.read_text(encoding="utf-8", errors="replace")
