from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from common import abs_path, run


CHROME_CANDIDATES = [
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
]


def asset_is_fresh(output_path: Path, source_paths: list[Path]) -> bool:
    if not output_path.exists() or output_path.stat().st_size <= 0:
        return False
    output_mtime = output_path.stat().st_mtime
    latest_source_mtime = max(path.stat().st_mtime for path in source_paths if path.exists())
    return output_mtime >= latest_source_mtime


def detect_chrome() -> Path:
    for candidate in CHROME_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit("Chrome or Chromium binary not found in standard macOS locations.")


def render_page(
    chrome: Path,
    html_path: Path,
    out_path: Path,
    width: int,
    height: int,
    profile_dir: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    source_paths = [html_path, html_path.parent / "marketing.css"]
    if asset_is_fresh(out_path, source_paths):
        return
    command = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-background-networking",
        "--hide-scrollbars",
        f"--user-data-dir={profile_dir}",
        f"--window-size={width},{height}",
        f"--screenshot={out_path}",
        html_path.as_uri(),
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        if out_path.exists() and out_path.stat().st_size > 0:
            return
        if process.poll() is not None:
            time.sleep(0.25)
            if out_path.exists() and out_path.stat().st_size > 0:
                return
            raise SystemExit(f"Chrome exited before writing {out_path}")
        time.sleep(0.25)
    raise SystemExit(f"Timed out waiting for {out_path}")


def convert_image(source: Path, destination: Path, image_format: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = run(["sips", "-s", "format", image_format, str(source), "--out", str(destination)], timeout=60)
    if result.returncode != 0:
        raise SystemExit(f"sips convert failed:\n{result.stderr or result.stdout}")


def render_jpeg(
    chrome: Path,
    html_path: Path,
    out_path: Path,
    width: int,
    height: int,
    profile_dir: Path,
) -> None:
    source_paths = [html_path, html_path.parent / "marketing.css"]
    if asset_is_fresh(out_path, source_paths):
        return
    temp_png = out_path.with_suffix(".render.png")
    try:
        render_page(chrome, html_path, temp_png, width, height, profile_dir)
        convert_image(temp_png, out_path, "jpeg")
    finally:
        temp_png.unlink(missing_ok=True)


def resize(source: Path, destination: Path, size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = run(["sips", "-z", str(size), str(size), str(source), "--out", str(destination)], timeout=60)
    if result.returncode != 0:
        raise SystemExit(f"sips resize failed:\n{result.stderr or result.stdout}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render icon and store assets from local HTML mockups.")
    parser.add_argument("--repo-root", default=".", help="Project root.")
    args = parser.parse_args()

    repo_root = abs_path(args.repo_root)
    chrome = detect_chrome()
    marketing = repo_root / "marketing"
    dist_assets = repo_root / "dist" / "store-assets"
    icons_dir = repo_root / "extension" / "icons"

    temp_icon = dist_assets / "icon128.png"
    screenshot = dist_assets / "locallens-store-screenshot-1.png"
    screenshot_alt = dist_assets / "locallens-store-screenshot-2.jpg"
    promo = dist_assets / "locallens-promo-small.png"
    marquee = dist_assets / "locallens-promo-marquee.jpg"

    profile_dir = Path(tempfile.mkdtemp(prefix="locallens-chrome-"))
    try:
        render_page(chrome, marketing / "icon.html", temp_icon, 128, 128, profile_dir)
        render_page(chrome, marketing / "screenshot.html", screenshot, 1280, 800, profile_dir)
        render_jpeg(chrome, marketing / "screenshot-focus.html", screenshot_alt, 1280, 800, profile_dir)
        render_page(chrome, marketing / "promo.html", promo, 440, 280, profile_dir)
        render_jpeg(chrome, marketing / "marquee.html", marquee, 1400, 560, profile_dir)

        icons_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_icon, icons_dir / "icon128.png")
        resize(temp_icon, icons_dir / "icon48.png", 48)
        resize(temp_icon, icons_dir / "icon32.png", 32)
        resize(temp_icon, icons_dir / "icon16.png", 16)
    finally:
        run(["pkill", "-f", str(profile_dir)], timeout=10)
        shutil.rmtree(profile_dir, ignore_errors=True)

    print(f"Generated store assets in {dist_assets}")
    print(f"Generated extension icons in {icons_dir}")


if __name__ == "__main__":
    main()
