from __future__ import annotations

import argparse
import os
import signal
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

POPUP_SCREENSHOT_STATES = {
    "page-summary": {
        "capability_status": "Summarizer: available • Prompt API: available",
        "download_status": "Finished locally. Nothing was sent to an external server.",
        "source_badge": "Page summary",
        "source_title": "Design review notes",
        "source_meta": "docs.example • 486 words captured from the active tab",
        "output": (
            "- LocalLens extracts readable text from the active tab only after a click.\n"
            "- The popup keeps the workflow inside Chrome with no account or API key.\n"
            "- Summaries appear as practical key points for fast scanning and handoff."
        ),
    },
    "translation": {
        "capability_status": "Summarizer: available • Prompt API: available",
        "download_status": "Finished locally. Nothing was sent to an external server.",
        "source_badge": "Translated selection",
        "source_title": "Selected launch copy",
        "source_meta": "product.example • 132 selected words",
        "output": (
            "Resumen en espanol:\n"
            "- El texto seleccionado se traduce dentro del popup.\n"
            "- Los nombres y enlaces se conservan cuando es posible.\n"
            "- No se necesita una cuenta ni un servicio remoto."
        ),
        "language": "Spanish",
    },
}


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
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    def stop_process() -> tuple[str, str]:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            return process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            return process.communicate()

    deadline = time.time() + 30
    while time.time() < deadline:
        if out_path.exists() and out_path.stat().st_size > 0:
            stop_process()
            return
        if process.poll() is not None:
            break
        time.sleep(0.25)

    if process.poll() is None:
        stdout, stderr = stop_process()
    else:
        stdout, stderr = process.communicate()

    if out_path.exists() and out_path.stat().st_size > 0:
        return
    if process.returncode not in (0, None):
        raise SystemExit(
            f"Chrome screenshot failed for {html_path}:\n{stderr or stdout}"
        )
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


def render_popup_screenshot(
    chrome: Path,
    repo_root: Path,
    out_path: Path,
    scenario: str,
    *,
    image_format: str = "png",
) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - environment-dependent
        raise SystemExit(f"Playwright is required to render popup screenshots: {exc}")

    state = POPUP_SCREENSHOT_STATES[scenario]
    popup_html = repo_root / "extension" / "popup.html"
    source_paths = [
        Path(__file__).resolve(),
        popup_html,
        repo_root / "extension" / "popup.css",
        repo_root / "extension" / "popup.js",
    ]
    if asset_is_fresh(out_path, source_paths):
        return

    temp_output = out_path if image_format == "png" else out_path.with_suffix(".render.png")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=str(chrome),
            args=["--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        page.goto(popup_html.as_uri(), wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_selector("#capability-status", timeout=30_000)
        page.evaluate(
            """(state) => {
                document.documentElement.style.width = "1280px";
                document.documentElement.style.height = "800px";
                document.body.style.display = "grid";
                document.body.style.placeItems = "center";
                document.body.style.width = "1280px";
                document.body.style.height = "800px";
                document.body.style.padding = "48px";
                document.body.style.overflow = "hidden";
                let style = document.getElementById("store-shot-overrides");
                if (!style) {
                  style = document.createElement("style");
                  style.id = "store-shot-overrides";
                  style.textContent = `
                    .shell {
                      width: 520px !important;
                      gap: 12px !important;
                    }
                    .hero,
                    .status-card,
                    .controls,
                    .source-card,
                    .output-card {
                      padding: 14px !important;
                    }
                    .hero {
                      gap: 12px !important;
                    }
                    .hero h1,
                    .controls h2,
                    .output-header h2 {
                      font-size: 24px !important;
                    }
                    .tagline,
                    .status-value,
                    .source-title,
                    .source-meta,
                    .download-status,
                    .output,
                    .translate-label,
                    select,
                    button {
                      font-size: 12px !important;
                    }
                    .button-grid button {
                      padding: 10px 12px !important;
                    }
                    .output-card {
                      min-height: auto !important;
                    }
                    .output {
                      min-height: 92px !important;
                      max-height: none !important;
                      padding: 12px !important;
                    }
                  `;
                  document.head.appendChild(style);
                }
                const shell = document.querySelector(".shell");
                if (shell) {
                  shell.style.margin = "0";
                }
                document.getElementById("capability-status").textContent = state.capability_status;
                document.getElementById("download-status").textContent = state.download_status;
                document.getElementById("source-badge").textContent = state.source_badge;
                document.getElementById("source-title").textContent = state.source_title;
                document.getElementById("source-meta").textContent = state.source_meta;
                document.getElementById("output").textContent = state.output;
                const language = state.language;
                if (language) {
                  const select = document.getElementById("target-language");
                  if (select) {
                    select.value = language;
                  }
                }
                if (shell) {
                  const availableWidth = 1280 - 96;
                  const availableHeight = 800 - 96;
                  const rect = shell.getBoundingClientRect();
                  const scale = Math.min(1, availableWidth / rect.width, availableHeight / rect.height);
                  shell.style.zoom = String(scale);
                }
            }""",
            state,
        )
        page.wait_for_timeout(150)
        page.screenshot(path=str(temp_output), full_page=False)
        browser.close()

    if image_format == "jpeg":
        try:
            convert_image(temp_output, out_path, "jpeg")
        finally:
            temp_output.unlink(missing_ok=True)


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
        render_popup_screenshot(chrome, repo_root, screenshot, "page-summary", image_format="png")
        render_popup_screenshot(chrome, repo_root, screenshot_alt, "translation", image_format="jpeg")
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
