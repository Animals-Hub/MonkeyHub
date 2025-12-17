#!/usr/bin/env python3
import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, Optional, Tuple

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI


def _sniff_kind(path: Path) -> str:
    head = path.read_bytes()[:16]
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "gif"
    return "unknown"


def _data_url_png_or_jpeg(path: Path) -> str:
    kind = _sniff_kind(path)
    if kind in ("png", "jpeg"):
        mime = "image/png" if kind == "png" else "image/jpeg"
        return f"data:{mime};base64,{_read_b64(path)}"
    if kind == "webp":
        sips = shutil.which("sips")
        if not sips:
            return f"data:image/png;base64,{_read_b64(path)}"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "converted.png"
            subprocess.run([sips, "-s", "format", "png", str(path), "--out", str(out)], check=True, capture_output=True)
            return f"data:image/png;base64,{_read_b64(out)}"
    return f"data:application/octet-stream;base64,{_read_b64(path)}"


def _read_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _iter_images(imgs_dir: Path) -> Iterable[Path]:
    for p in sorted(imgs_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".gif":
            continue
        yield p


def _load_done_inputs(manifest_path: Path) -> set[str]:
    done: set[str] = set()
    if not manifest_path.exists():
        return done
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("ok") is True and isinstance(obj.get("input"), str):
            done.add(obj["input"])
    return done


def _extract_image_payload(text: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Returns (url, bytes) where exactly one may be present.
    Supports:
      - data:image/...;base64,...
      - raw URL in text (common for local gateway endpoints)
    """
    m = re.search(r"(data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+)", text)
    if m:
        data_url = m.group(1)
        b64 = data_url.split(",", 1)[1]
        return None, base64.b64decode(b64)

    # markdown image: ![image](https://...)
    m = re.search(r"!\\[[^\\]]*\\]\\((https?://[^\\s)]+)\\)", text)
    if m:
        return m.group(1), None

    m = re.search(r"(https?://\\S+)", text)
    if m:
        return m.group(1).rstrip(").,]\"'"), None
    return None, None


def _default_ref() -> str:
    return "monkey-ip-compress.png" if Path("monkey-ip-compress.png").exists() else "monkey-ip.png"


def _out_name(in_path: Path) -> str:
    # Replace Pig with Monkey in the filename
    stem = in_path.stem.replace("猪", "猴")
    
    ext = in_path.suffix.lower().lstrip(".")
    if ext == "png":
        return f"{stem}.png"
    return f"{stem}__{ext}.png"


def _build_prompt() -> str:
    return (
        """
任务：将图1中的“猪”替换为图2中的 Monkey 角色。

合成要求：
- 仅替换主体：猪本体及与猪相关的附属部件/装饰（若有）。
- 几何匹配：Monkey 的缩放、位置、朝向、透视与图1原猪完全一致。
- 光影匹配：严格匹配图1的主光方向、亮度、色温、对比度；保留并重建接触阴影/投影，使其与地面/物体接触自然。
- 质感融合：边缘无硬切、无白边/黑边；细节清晰，不出现抹糊或涂抹感；整体观感与图1一致。
- 保证图2中文字的清晰度、清晰度与图1一致。
- 动作匹配：图2中的 Monkey 动作与图1中的猪动作一致。
- 情绪匹配：图2中的 Monkey 情绪与图1中的猪情绪一致。
- 语言匹配：图2中的 Monkey 语言与图1中的猪语言一致。
- 角色匹配：图2中的 Monkey 角色与图1中的猪角色一致。
- 角色属性匹配：图2中的 Monkey 属性与图1中的猪属性一致。
- 角色关系匹配：图2中的 Monkey 关系与图1中的猪关系一致。
- 角色行为匹配：图2中的 Monkey 行为与图1中的猪行为一致。
- 角色表情匹配：图2中的 Monkey 表情与图1中的猪表情一致。
- 角色服装匹配：图2中的 Monkey 服装与图1中的猪服装一致。
- 角色物品匹配：图2中的 Monkey 物品与图1中的猪物品一致。
- 角色场景匹配：图2中的 Monkey 场景与图1中的猪场景一致。
- 角色背景匹配：图2中的 Monkey 背景与图1中的猪背景一致。
- 角色动作匹配：图2中的 Monkey 动作与图1中的猪动作一致。
- 角色姿态匹配：图2中的 Monkey 姿态与图1中的猪姿态一致。

文字/标识处理：
- 图1中任何包含“猪”字样或指代猪的文字、标识、贴纸、图案等，全部替换为与 Monkey 对应的元素（如“猴”字样或 Monkey 相关图形/符号），风格、字体粗细、颜色、材质与原始一致，排版位置不变。

严格限制：
- 不裁剪、不加边框、不改变画布尺寸与分辨率。
- 不改变背景、不做全局调色、不新增除 Monkey 及其必要阴影/反射之外的元素。
- 保持图1其余内容完全不变。

输出：
- 仅输出最终合成后的 PNG 图片；不输出任何解释文字或步骤。
        """
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Batch: replace IP/watermark with monkey-ip.png via AI (skip GIF).")
    parser.add_argument("--imgs-dir", default="imgs", help="Input directory (default: imgs)")
    parser.add_argument("--out-dir", default="imgs_monkey", help="Output directory (default: imgs_monkey)")
    parser.add_argument("--ref", default=_default_ref(), help="Reference image for replacement")
    parser.add_argument("--model", default="gemini-3-pro-preview", help="Model name (default: gemini-3-pro-preview)")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent generations (default: 3)")
    parser.add_argument("--timeout", type=int, default=900, help="Per-request timeout seconds (default: 900)")
    parser.add_argument("--retries", type=int, default=2, help="Retries per image on failure (default: 2)")
    parser.add_argument("--retry-delay", type=float, default=3.0, help="Seconds between retries (default: 3.0)")
    parser.add_argument("--limit", type=int, default=0, help="Only process first N images (default: 0 = all)")
    parser.add_argument("--no-resume", action="store_true", help="Do not skip already-processed inputs")
    args = parser.parse_args()

    load_dotenv(dotenv_path=Path(".env"))
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise SystemExit("Missing OPENAI_BASE_URL / OPENAI_API_KEY in .env (or environment).")

    imgs_dir = Path(args.imgs_dir)
    if not imgs_dir.exists():
        raise SystemExit(f"Input directory not found: {imgs_dir}")

    ref_path = Path(args.ref)
    if not ref_path.exists():
        raise SystemExit(f"Reference image not found: {ref_path}")
    if ref_path.stat().st_size > 2_000_000:
        print(f"Warning: reference image is large ({ref_path.stat().st_size} bytes); consider using a smaller ref.")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"
    failed_path = out_dir / "failed.txt"

    done = set() if args.no_resume else _load_done_inputs(manifest_path)
    inputs = [p for p in _iter_images(imgs_dir) if str(p) not in done]
    if args.limit and args.limit > 0:
        inputs = inputs[: args.limit]

    print(f"Model={args.model}")
    print(f"Input images (new): {len(inputs)}")
    print(f"Output dir: {out_dir}")

    client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=args.timeout)
    prompt = _build_prompt()

    ref_data_url = _data_url_png_or_jpeg(ref_path)

    sem = asyncio.Semaphore(max(1, args.concurrency))
    lock = asyncio.Lock()
    progress = {"done": 0, "total": len(inputs)}

    async with httpx.AsyncClient(timeout=args.timeout) as http:

        async def process_one(in_path: Path) -> None:
            async with sem:
                out_name = _out_name(in_path)
                out_path = out_dir / out_name
                in_data_url = _data_url_png_or_jpeg(in_path)

                rec = {"input": str(in_path), "output": str(out_path), "ok": False, "model": args.model}
                try:
                    for attempt in range(args.retries + 1):
                        try:
                            resp = await client.chat.completions.create(
                                model=args.model,
                                temperature=0,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt},
                                            {"type": "image_url", "image_url": {"url": in_data_url}},  # 图1
                                            {"type": "image_url", "image_url": {"url": ref_data_url}},  # 图2
                                        ],
                                    }
                                ],
                            )
                            content = resp.choices[0].message.content
                            if isinstance(content, list):
                                content = "\n".join(str(x) for x in content)
                            if not isinstance(content, str):
                                content = str(content)

                            url, data = _extract_image_payload(content)
                            if data is not None:
                                out_path.write_bytes(data)
                                rec["ok"] = True
                                break
                            if url:
                                r = await http.get(url)
                                r.raise_for_status()
                                out_path.write_bytes(r.content)
                                rec["ok"] = True
                                rec["url"] = url
                                break
                            raise RuntimeError("Model response didn't include image URL/base64")
                        except Exception as e:
                            if attempt < args.retries:
                                await asyncio.sleep(args.retry-delay)
                                continue
                            raise
                except Exception as e:
                    rec["error"] = str(e)
                    async with lock:
                        with failed_path.open("a", encoding="utf-8") as f:
                            f.write(f"{in_path}\t{e}\n")
                finally:
                    async with lock:
                        with manifest_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        progress["done"] += 1
                        if progress["done"] % 10 == 0 or progress["done"] == progress["total"]:
                            ok = "ok" if rec.get("ok") else "fail"
                            print(f"[{progress['done']}/{progress['total']}] {ok}: {in_path.name}")

        await asyncio.gather(*(process_one(p) for p in inputs))

    print("Done.")
    print(f"Manifest: {manifest_path}")
    if failed_path.exists():
        print(f"Failures: {failed_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
