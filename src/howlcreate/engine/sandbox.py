"""An explicit, escape-resistant output root for materialized artifacts.

Materialization is file creation inside one directory the operator names,
and nothing else: no subprocess, no git, no network, no writes outside
the root. Containment is enforced by the kernel, not by string prefixes.
The root is opened once with ``O_NOFOLLOW | O_DIRECTORY`` and every file
is created relative to that descriptor, one path component at a time, each
opened with ``O_NOFOLLOW``. A symlink planted anywhere under the root (or
swapped in during the write) therefore fails the open instead of being
followed.

By default the root may not sit inside a git work tree, so a sandbox can
never be pointed at a live source repository by accident.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path, PurePosixPath

_DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_FILE_FLAGS = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
ALLOWED_SUFFIXES = frozenset({".html", ".css", ".js", ".json", ".md", ".txt", ".svg"})
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 64
ALLOWLIST_ENV = "HOWLCREATE_SANDBOX_ROOTS"


class SandboxError(PermissionError):
    """A materialization target was refused."""


def _git_work_tree(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _allowlisted_roots() -> list[Path]:
    raw = os.environ.get(ALLOWLIST_ENV, "")
    return [Path(p).resolve() for p in raw.split(os.pathsep) if p.strip()]


def validate_relative(name: str) -> PurePosixPath:
    """A safe artifact path: relative, no '..', no NUL, an allowed file type."""
    if not isinstance(name, str) or not name or "\0" in name or "\\" in name:
        raise SandboxError(f"invalid artifact path {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or name.startswith("~"):
        raise SandboxError(f"absolute artifact path denied: {name}")
    if any(part in {"..", ".", ""} for part in path.parts):
        raise SandboxError(f"path traversal denied: {name}")
    if path.parts[0] == ".git" or any(part.startswith(".git") for part in path.parts):
        raise SandboxError(f"git metadata path denied: {name}")
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise SandboxError(f"artifact type {path.suffix or '(none)'} not allowed: {name}")
    return path


class SandboxRoot:
    """An operator-approved directory that artifacts may be written into."""

    def __init__(self, root: str | os.PathLike, *, allow_repo: bool = False, replace: bool = False):
        if not str(root).strip():
            raise SandboxError("an explicit --output-dir is required")
        raw = Path(root).expanduser()
        if raw.is_symlink():
            raise SandboxError(f"sandbox root is a symlink: {raw}")
        parent = raw.parent.resolve(strict=True) if raw.parent != raw else raw
        resolved = parent / raw.name if raw.name else parent
        if resolved in {Path("/"), Path.home().resolve()} or len(resolved.parts) < 3:
            raise SandboxError(f"sandbox root too broad: {resolved}")
        allowlist = _allowlisted_roots()
        if allowlist and not any(resolved == a or resolved.is_relative_to(a) for a in allowlist):
            raise SandboxError(f"sandbox root {resolved} is outside {ALLOWLIST_ENV}")
        repo = _git_work_tree(resolved)
        if repo is not None and not allow_repo:
            raise SandboxError(
                f"sandbox root {resolved} is inside the git work tree {repo}; "
                "live repository materialization is denied by default"
            )
        if resolved.exists():
            mode = os.lstat(resolved).st_mode
            if not stat.S_ISDIR(mode):
                raise SandboxError(f"sandbox root is not a directory: {resolved}")
            if any(resolved.iterdir()) and not replace:
                raise SandboxError(f"sandbox root is not empty: {resolved} (pass --replace)")
        else:
            os.mkdir(resolved, 0o755)
        self.path = resolved
        self.allow_repo = allow_repo
        self._written: list[str] = []

    def _open_dir(self, fd: int, name: str, create: bool) -> int:
        if create:
            try:
                os.mkdir(name, 0o755, dir_fd=fd)
            except FileExistsError:
                pass
        try:
            return os.open(name, _DIR_FLAGS, dir_fd=fd)
        except OSError as error:
            raise SandboxError(f"refused directory component {name!r}: {error.strerror}") from None

    def write(self, name: str, data: bytes) -> Path:
        """Create or replace one file under the root without following symlinks."""
        path = validate_relative(name)
        if len(data) > MAX_FILE_BYTES:
            raise SandboxError(f"artifact {name} exceeds {MAX_FILE_BYTES} bytes")
        if name not in self._written and len(self._written) >= MAX_FILES:
            raise SandboxError(f"materialization exceeds {MAX_FILES} files")
        root_fd = os.open(self.path, _DIR_FLAGS)
        fds = [root_fd]
        try:
            for part in path.parts[:-1]:
                fds.append(self._open_dir(fds[-1], part, create=True))
            leaf = path.parts[-1]
            try:
                existing = os.stat(leaf, dir_fd=fds[-1], follow_symlinks=False)
            except FileNotFoundError:
                existing = None
            if existing is not None and not stat.S_ISREG(existing.st_mode):
                raise SandboxError(f"refused to replace non-regular file {name}")
            try:
                fd = os.open(leaf, _FILE_FLAGS | os.O_TRUNC, 0o644, dir_fd=fds[-1])
            except OSError as error:
                raise SandboxError(f"refused artifact {name}: {error.strerror}") from None
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        finally:
            for fd in reversed(fds):
                os.close(fd)
        if name not in self._written:
            self._written.append(name)
        return self.path / path

    @property
    def written(self) -> list[str]:
        return list(self._written)
