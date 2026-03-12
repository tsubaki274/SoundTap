from __future__ import annotations

import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT_DIR / "dist"
RELEASE_DIR = ROOT_DIR / "release"


def main() -> int:
    exe_path = DIST_DIR / "SoundTap.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"Built executable was not found: {exe_path}")

    RELEASE_DIR.mkdir(exist_ok=True)
    target_path = RELEASE_DIR / exe_path.name
    shutil.copy2(exe_path, target_path)

    readme_source = ROOT_DIR / "README.md"
    shutil.copy2(readme_source, RELEASE_DIR / "README.md")

    print(target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
