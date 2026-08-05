"""Friday — modular AI assistant backend with composable intelligence primitives."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from friday.sdk import Friday, FridaySystem, MemoryHandle, SystemBuilder

try:
    __version__ = _pkg_version("friday")
except PackageNotFoundError:  # pragma: no cover — uninstalled source tree
    __version__ = "0.0.0+unknown"

__all__ = ["Friday", "FridaySystem", "MemoryHandle", "SystemBuilder", "__version__"]
