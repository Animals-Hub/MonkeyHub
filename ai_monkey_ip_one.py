#!/usr/bin/env python3
import argparse
import base64
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv
from openai import OpenAI


def _read_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")

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
            # Fallback: some gateways still accept this, even if the bytes are webp.
            return f"data:image/png;base64,{_read_b64(path)}"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "converted.png"
            subprocess.run([sips, "-s", "format", "png", str(path), "--out", str(out)], check=True, capture_output=True)
            return f"data:image/png;base64,{_read_b64(out)}"
    return f"data:application/octet-stream;base64,{_read_b64(path)}"


def _first_non_gif(imgs_dir: Path) -> Optional[Path]:
    for p in sorted(imgs_dir.iterdir()):
        if p.is_file() and p.suffix.lower() != ".gif":
            return p
    return None


def _extract_image_payload(text: str) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Returns (url, bytes) where exactly one may be present.
    Supports:
      - data:image/...;base64,...
      - raw URL in text
    """
    m = re.search(r"(data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=]+)", text)
    if m:
        data_url = m.group(1)
        b64 = data_url.split(",", 1)[1]
        return None, base64.b64decode(b64)

    m = re.search(r"(https?://\\S+)", text)
    if m:
        return m.group(1).rstrip(").,]\"'"), None
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Test: transform one image by replacing IP to @monkey-ip.png via AI.")
    parser.add_argument("--input", help="Input image path; default picks first non-gif in imgs/")
    parser.add_argument("--imgs-dir", default="imgs", help="Directory to auto-pick input from (default: imgs)")
    default_ref = "monkey-ip-compress.png" if Path("monkey-ip-compress.png").exists() else "monkey-ip.png"
    parser.add_argument("--ref", default=default_ref, help=f"Reference image for replacement (default: {default_ref})")
    parser.add_argument("--out", default="out_test_monkey.png", help="Output file path (default: out_test_monkey.png)")
    parser.add_argument("--model", default="gemini-3-pro-preview", help="Model name (default: gemini-3-pro-preview)")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout seconds (default: 600)")
    args = parser.parse_args()

    load_dotenv(dotenv_path=Path(".env"))
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise SystemExit("Missing OPENAI_BASE_URL / OPENAI_API_KEY in .env (or environment).")

    imgs_dir = Path(args.imgs_dir)
    in_path = Path(args.input) if args.input else _first_non_gif(imgs_dir)
    if not in_path or not in_path.exists():
        raise SystemExit("Input image not found. Use --input or ensure imgs/ has images.")

    ref_path = Path(args.ref)
    if not ref_path.exists():
        raise SystemExit(f"Reference image not found: {ref_path}")

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=args.timeout)

    # Send both images: base image + sticker/reference image.
    in_data_url = _data_url_png_or_jpeg(in_path)
    ref_data_url = _data_url_png_or_jpeg(ref_path)

    prompt = (
        """
任务：将图1中的“猪”替换为图2中的 Monkey 角色。

合成要求：
- 仅替换主体：猪本体及与猪相关的附属部件/装饰（若有）。
- 几何匹配：Monkey 的缩放、位置、朝向、透视与图1原猪完全一致。
- 光影匹配：严格匹配图1的主光方向、亮度、色温、对比度；保留并重建接触阴影/投影，使其与地面/物体接触自然。
- 质感融合：边缘无硬切、无白边/黑边；细节清晰，不出现抹糊或涂抹感；整体观感与图1一致。

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

    print(f"Using model={args.model}")
    print(f"Input: {in_path} ({in_path.stat().st_size} bytes)")
    print(f"Ref:   {ref_path} ({ref_path.stat().st_size} bytes)")
    print("Sending request...")

    resp = client.chat.completions.create(
        model=args.model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": in_data_url}},  # 图A
                    {"type": "image_url", "image_url": {"url": ref_data_url}},  # 图B
                ],
            }
        ],
    )

    print("Got response; extracting image...")

    content = resp.choices[0].message.content
    if isinstance(content, list):
        content = "\n".join(str(x) for x in content)
    if not isinstance(content, str):
        content = str(content)

    url, data = _extract_image_payload(content)
    out_path = Path(args.out)

    if data is not None:
        out_path.write_bytes(data)
    elif url:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        out_path.write_bytes(r.content)
    else:
        raise SystemExit(f"Model response didn't include an image URL/base64. Raw content:\n{content}")

    print(f"OK: {in_path} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
