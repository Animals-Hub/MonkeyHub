#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import json
import mimetypes
import re
from pathlib import Path
from typing import Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from playwright.async_api import async_playwright


DEFAULT_URL = "https://www.pighub.top/all"


def _clean_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if url.startswith("data:") or url.startswith("blob:") or url.startswith("javascript:"):
        return ""
    parsed = urlparse(url)
    parsed = parsed._replace(fragment="")
    return urlunparse(parsed)


def _is_probably_image_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(
        path.endswith(ext)
        for ext in (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".bmp",
            ".svg",
            ".avif",
            ".heic",
        )
    )


def _safe_stem(text: str, max_len: int = 80) -> str:
    text = re.sub(r"[^\w.-]+", "_", text, flags=re.UNICODE).strip("._")
    if not text:
        text = "image"
    return text[:max_len]


def _guess_ext(url: str, content_type: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix
    if suffix and len(suffix) <= 6:
        return suffix
    content_type = (content_type or "").split(";")[0].strip().lower()
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/avif": ".avif",
        "image/bmp": ".bmp",
        "image/heic": ".heic",
    }
    if content_type in mapping:
        return mapping[content_type]
    guessed = mimetypes.guess_extension(content_type) if content_type else None
    return guessed or ".img"


async def _extract_image_urls(page, base_url: str) -> list[str]:
    raw_urls: list[str] = await page.evaluate(
        """
      () => {
        function pickFromSrcset(srcset) {
          // Pick the last candidate (usually highest resolution).
          const parts = (srcset || "").split(",").map(s => s.trim()).filter(Boolean);
          if (!parts.length) return "";
          const last = parts[parts.length - 1];
          return last.split(/\\s+/)[0] || "";
        }

        const out = new Set();
        const imgAttrs = ["src", "data-src", "data-lazy-src", "data-original", "data-url", "data-img"];

        for (const img of document.querySelectorAll("img")) {
          for (const a of imgAttrs) {
            const v = img.getAttribute(a);
            if (v) out.add(v);
          }
          const ss = img.getAttribute("srcset");
          if (ss) out.add(pickFromSrcset(ss));
        }

        for (const source of document.querySelectorAll("source")) {
          const ss = source.getAttribute("srcset");
          if (ss) out.add(pickFromSrcset(ss));
        }

        for (const el of document.querySelectorAll('[style*="background-image"]')) {
          const bg = el.style && el.style.backgroundImage ? el.style.backgroundImage : "";
          const m = /url\\((['"]?)(.*?)\\1\\)/.exec(bg);
          if (m && m[2]) out.add(m[2]);
        }

        return Array.from(out).filter(Boolean);
      }
    """
    )

    cleaned: list[str] = []
    for u in raw_urls:
        u = _clean_url(str(u))
        if not u:
            continue
        if u.startswith("//"):
            parsed = urlparse(base_url)
            u = f"{parsed.scheme}:{u}"
        u = urljoin(base_url, u)
        u = _clean_url(u)
        if u:
            cleaned.append(u)

    # Prefer likely images, but keep everything (some CDNs hide extensions).
    cleaned.sort(key=lambda x: (0 if _is_probably_image_url(x) else 1, x))
    return cleaned


async def _load_more_status(page) -> Tuple[bool, bool]:
    locator = page.locator(
        "button:has-text('加载更多猪猪'), a:has-text('加载更多猪猪'), [role=button]:has-text('加载更多猪猪')"
    )
    if await locator.count() == 0:
        locator = page.locator("text=加载更多猪猪")
    present = (await locator.count()) > 0
    if not present:
        return False, False
    try:
        visible = await locator.first.is_visible()
    except Exception:
        return True, False
    if not visible:
        return True, False
    try:
        await locator.first.scroll_into_view_if_needed()
        await locator.first.click(timeout=3000)
        return True, True
    except Exception:
        return True, False


async def _auto_load_all(page, base_url: str, max_rounds: int, settle_rounds: int, pause_ms: int) -> list[str]:
    seen: set[str] = set()
    stable = 0

    for _ in range(max_rounds):
        urls = await _extract_image_urls(page, base_url)
        before = len(seen)
        seen.update(urls)
        after = len(seen)
        if after == before:
            stable += 1
        else:
            stable = 0

        present, clicked = await _load_more_status(page)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(pause_ms)

        # If the page isn't changing anymore and the button is gone, stop.
        if stable >= settle_rounds and not present:
            break

    return sorted(seen)


def _load_existing_manifest(manifest_path: Path) -> set[str]:
    urls: set[str] = set()
    if not manifest_path.exists():
        return urls
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            u = obj.get("url")
            if isinstance(u, str) and u:
                urls.add(u)
        except Exception:
            continue
    return urls


async def main() -> int:
    parser = argparse.ArgumentParser(description="Download all images from pighub/all (handles '加载更多猪猪' lazy load).")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Target page URL (default: {DEFAULT_URL})")
    parser.add_argument("--out", default="imgs", help="Output directory (default: imgs)")
    parser.add_argument("--headful", action="store_true", help="Run with a visible browser window")
    parser.add_argument("--max-rounds", type=int, default=300, help="Max load-more/scroll rounds (default: 300)")
    parser.add_argument("--settle-rounds", type=int, default=6, help="Stop after N stable rounds (default: 6)")
    parser.add_argument("--pause-ms", type=int, default=1200, help="Pause between rounds in ms (default: 1200)")
    parser.add_argument("--concurrency", type=int, default=8, help="Concurrent downloads (default: 8)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"
    failed_path = out_dir / "failed.txt"
    existing_urls = _load_existing_manifest(manifest_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not args.headful)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(args.url, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("img", timeout=15000)
        except Exception:
            pass

        urls = await _auto_load_all(
            page, base_url=args.url, max_rounds=args.max_rounds, settle_rounds=args.settle_rounds, pause_ms=args.pause_ms
        )
        urls = [u for u in urls if u not in existing_urls]

        print(f"Found {len(urls) + len(existing_urls)} image URLs total; downloading {len(urls)} new...")

        sem = asyncio.Semaphore(max(1, args.concurrency))
        lock = asyncio.Lock()

        async def download_one(idx: int, url: str) -> None:
            async with sem:
                url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
                basename = Path(urlparse(url).path).name or "image"
                stem = _safe_stem(Path(basename).stem)

                try:
                    resp = await context.request.get(url, timeout=60000)
                    if not resp.ok:
                        raise RuntimeError(f"HTTP {resp.status}")
                    body = await resp.body()
                    ext = _guess_ext(url, resp.headers.get("content-type", ""))

                    filename = f"{idx:06d}_{stem}_{url_hash}{ext}"
                    filepath = out_dir / filename
                    filepath.write_bytes(body)

                    async with lock:
                        with manifest_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps({"url": url, "file": filename}, ensure_ascii=False) + "\n")
                except Exception as e:
                    async with lock:
                        with failed_path.open("a", encoding="utf-8") as f:
                            f.write(f"{url}\t{e}\n")

        await asyncio.gather(*(download_one(i + 1, u) for i, u in enumerate(urls)))

        await context.close()
        await browser.close()

    print(f"Done. Files saved to: {out_dir.resolve()}")
    if failed_path.exists():
        print(f"Some downloads failed; see: {failed_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
