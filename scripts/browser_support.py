"""Optional rootless compatibility libraries for this Ubuntu 26.04 workstation."""

import os
from pathlib import Path


def configure_browser():
    libs = Path("/tmp/opencode/browser-libs/usr/lib/x86_64-linux-gnu")
    if libs.is_dir():
        os.environ["LD_LIBRARY_PATH"] = str(libs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
    os.environ.setdefault("PLAYWRIGHT_HOST_PLATFORM_OVERRIDE", "ubuntu24.04-x64")
