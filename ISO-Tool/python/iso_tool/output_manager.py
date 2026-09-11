"""User-selected ISO output and generated-artifact folder management."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys

@dataclass(frozen=True)
class OutputLayout:
    root: Path
    iso: Path
    boot_images: Path
    executables: Path
    libraries: Path
    logs: Path
    manifests: Path


def default_output_root() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "Downloads" / "Chimera-II-ISO-Tool"


def create_output_layout(root: str | Path) -> OutputLayout:
    base = Path(root).expanduser().resolve()
    paths = {"iso": base / "iso", "boot_images": base / "boot-images", "executables": base / "binaries" / "executables", "libraries": base / "binaries" / "libraries", "logs": base / "logs", "manifests": base / "manifests"}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return OutputLayout(base, **paths)


def choose_output_directory(parent=None, initial: str | Path | None = None) -> Path:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk(); root.withdraw()
    try:
        selected = filedialog.askdirectory(parent=parent or root, title="Choose ISO-Tool generated output directory", initialdir=str(initial or default_output_root()), mustexist=False)
        if not selected:
            raise RuntimeError("ISO generation cancelled: no output directory selected")
        return Path(selected).expanduser().resolve()
    finally:
        root.destroy()


def reveal_path(path: str | Path) -> None:
    target = Path(path).resolve()
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer.exe", "/select,", str(target)] if target.is_file() else ["explorer.exe", str(target)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])
