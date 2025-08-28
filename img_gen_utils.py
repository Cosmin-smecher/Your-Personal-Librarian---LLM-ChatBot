# -*- coding: utf-8 -*-
"""
img_gen_utils.py — Image generation helper for books
- Uses OpenAI Images API (gpt-image-1) to create a representative cover/scene.
- Fallback: creates a simple placeholder image locally (Pillow) if API fails.
"""
from __future__ import annotations
from typing import Tuple
import base64
from io import BytesIO

def _build_prompt(title: str, author: str, themes: str, summary: str, style: str) -> str:
    # Keep it brief and steer the model toward original, suggestive art (no logos)
    style_map = {
        "copertă minimală": "minimalist book cover, modern graphic shapes, clean typography, high contrast, subtle texture",
        "scenă cinematică": "cinematic wide scene, dramatic lighting, volumetric fog, detailed environment",
        "ilustrație acquarela": "watercolor illustration, soft edges, paper texture, gentle palette",
        "poster vintage": "vintage poster, retro print textures, bold typography, grainy look",
    }
    style_hint = style_map.get(style, style_map["copertă minimală"])
    core = f"""Create an original, copyright-safe illustration inspired by the book below.
Focus on atmosphere and themes, avoid text or logos, no copyrighted covers.
Book: "{title}" by {author}. Themes: {themes}.
Short context: {summary[:450]}
Art direction: {style_hint}. Highly detailed, professional quality, coherent composition.
"""
    return core

def generate_book_image(title: str, author: str, themes: str, summary: str, style: str = "copertă minimală", size: str = "1024x1024") -> Tuple[bytes, str, str]:
    """
    Returns (image_bytes, mime, used_prompt). Tries OpenAI first; if it fails, returns a local placeholder PNG.
    """
    prompt = _build_prompt(title or "", author or "", themes or "", summary or "", style or "copertă minimală")
    # Try OpenAI Images
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=size,
            quality="high",
        )
        b64 = resp.data[0].b64_json
        img_bytes = base64.b64decode(b64)
        return img_bytes, "image/png", prompt
    except Exception:
        # Fallback placeholder using Pillow
        try:
            from PIL import Image, ImageDraw, ImageFont, ImageFilter
            # Parse size like "1024x1024"
            try:
                w, h = [int(x) for x in size.lower().split("x")]
            except Exception:
                w, h = 1024, 1024
            img = Image.new("RGB", (w, h), (24, 26, 27))
            # simple gradient
            for y in range(h):
                blend = int(255 * (y / max(1, h-1)))
                for x in range(w):
                    img.putpixel((x, y), (24, 26, 27 + blend // 6))
            draw = ImageDraw.Draw(img)
            # Title block
            pad = int(min(w, h) * 0.06)
            rect_h = int(h * 0.34)
            draw.rounded_rectangle((pad, pad, w-pad, pad+rect_h), radius=24, fill=(46, 196, 182))
            # Text
            def _fit_text(text, max_w, base=48):
                size = base
                while size > 18:
                    try:
                        font = ImageFont.truetype("arial.ttf", size)
                    except Exception:
                        font = ImageFont.load_default()
                    tw, th = draw.multiline_textsize(text, font=font)
                    if tw <= max_w: 
                        return font
                    size -= 2
                return ImageFont.load_default()
            ttitle = (title or "Carte recomandată").strip()[:60]
            font = _fit_text(ttitle, w - 2*pad - 20, base=int(min(w, h) * 0.065))
            draw.multiline_text((pad+14, pad+14), ttitle, font=font, fill=(15, 23, 42))
            # Author & themes
            at = f"{author}".strip()[:36] if author else ""
            if at:
                draw.text((pad+14, pad+rect_h-40), at, fill=(15,23,42))
            # Save
            bio = BytesIO()
            img = img.filter(ImageFilter.SMOOTH_MORE)
            img.save(bio, format="PNG")
            return bio.getvalue(), "image/png", prompt
        except Exception:
            return b"", "image/png", prompt
