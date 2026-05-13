"""
Generate print-ready product designs using Pillow.
Produces PNG images for Printful print-on-demand fulfillment.
"""

import io
import os
import hashlib
from PIL import Image, ImageDraw, ImageFont


# Color palettes: (bg_rgb, text_rgb, accent_rgb, sub_rgb)
PALETTES = [
    {"bg": (26, 26, 46),    "text": (255, 255, 255), "accent": (124, 131, 253), "sub": (160, 168, 255)},
    {"bg": (13, 13, 13),    "text": (255, 255, 255), "accent": (255, 107, 53),  "sub": (255, 179, 71)},
    {"bg": (248, 248, 248), "text": (26, 26, 46),    "accent": (124, 131, 253), "sub": (85, 85, 119)},
    {"bg": (27, 67, 50),    "text": (216, 243, 220), "accent": (82, 183, 136),  "sub": (149, 213, 178)},
    {"bg": (74, 25, 66),    "text": (255, 255, 255), "accent": (247, 37, 133),  "sub": (220, 100, 200)},
    {"bg": (3, 4, 94),      "text": (202, 240, 248), "accent": (0, 180, 216),   "sub": (144, 224, 239)},
    {"bg": (255, 243, 224), "text": (62, 39, 35),    "accent": (255, 111, 0),   "sub": (191, 54, 12)},
    {"bg": (38, 50, 56),    "text": (236, 239, 241), "accent": (0, 188, 212),   "sub": (128, 222, 234)},
]

# Size per Printful product category
# portrait: shirts, hoodies, posters, phone cases
# square:   totes, canvas, notebooks, hats
# mug:      mugs (wide wrap format)
CATALOG_SHAPES = {
    "unisex_tshirt":     "portrait",
    "premium_tshirt":    "portrait",
    "hoodie":            "portrait",
    "mug_11oz":          "mug",
    "mug_15oz":          "mug",
    "tote_bag":          "square",
    "phone_case_iphone": "portrait",
    "poster_12x16":      "portrait",
    "canvas_16x20":      "portrait",
    "embroidered_hat":   "square",
    "notebook":          "square",
    "sticker_sheet":     "portrait",
}

SHAPE_SIZES = {
    "portrait": (1800, 2400),
    "square":   (2000, 2000),
    "mug":      (2700, 900),
}

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:\\Windows\\Fonts\\arialbd.ttf",
]

FONT_LIGHT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
]


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    paths = FONT_PATHS if bold else FONT_LIGHT_PATHS
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.Draw, text: str, font, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _pick_palette(seed: str) -> dict:
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(PALETTES)
    return PALETTES[idx]


class DesignGenerator:
    """Generate print-ready PNG designs for Printful POD products."""

    def generate(
        self,
        product_name: str,
        tagline: str,
        catalog_key: str = "",
        product_type: str = "",
    ) -> bytes:
        """
        Return raw PNG bytes for a print-ready Printful design.
        The design uses the product name + tagline as the visual content.
        """
        shape = CATALOG_SHAPES.get(catalog_key, "portrait")
        w, h = SHAPE_SIZES[shape]
        palette = _pick_palette(product_name)

        img = Image.new("RGB", (w, h), palette["bg"])
        draw = ImageDraw.Draw(img)

        if shape == "mug":
            self._draw_mug_layout(draw, product_name, tagline, w, h, palette)
        else:
            self._draw_standard_layout(draw, product_name, tagline, w, h, palette)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=False)
        return buf.getvalue()

    def _draw_standard_layout(self, draw, name, tagline, w, h, p):
        margin = max(60, w // 30)
        inner_w = w - margin * 2

        # Outer border frame
        draw.rectangle([margin, margin, w - margin, h - margin],
                       outline=p["accent"], width=5)

        # Accent header bar
        bar_h = max(50, h // 20)
        draw.rectangle([margin + 15, margin + 15,
                        w - margin - 15, margin + 15 + bar_h],
                       fill=p["accent"])

        # Product name — large, uppercase, centered
        name_upper = name.upper()
        name_font_size = max(80, w // 10)
        name_font = _load_font(name_font_size, bold=True)

        # Scale down font until it fits in 2 lines or fewer
        while name_font_size > 40:
            name_font = _load_font(name_font_size, bold=True)
            lines = _wrap_text(draw, name_upper, name_font, inner_w - margin)
            if len(lines) <= 3:
                break
            name_font_size -= 8

        name_lines = _wrap_text(draw, name_upper, name_font, inner_w - margin)
        line_h = name_font_size + int(name_font_size * 0.2)
        name_block_h = len(name_lines) * line_h

        # Center the name block vertically (slightly above center)
        y = (h - name_block_h) // 2 - int(h * 0.05)
        y = max(margin + bar_h + 40, y)

        for line in name_lines:
            bbox = draw.textbbox((0, 0), line, font=name_font)
            x = (w - (bbox[2] - bbox[0])) // 2
            # Subtle drop shadow
            draw.text((x + 3, y + 3), line, fill=(0, 0, 0), font=name_font)
            draw.text((x, y), line, fill=p["text"], font=name_font)
            y += line_h

        # Divider
        y += int(h * 0.025)
        draw.rectangle([margin + w // 6, y, w - margin - w // 6, y + 3],
                       fill=p["accent"])
        y += int(h * 0.04)

        # Tagline — smaller, centered
        tag_font_size = max(36, w // 22)
        tag_font = _load_font(tag_font_size, bold=False)
        tag_lines = _wrap_text(draw, tagline, tag_font, inner_w - margin)

        for line in tag_lines:
            bbox = draw.textbbox((0, 0), line, font=tag_font)
            x = (w - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, fill=p["sub"], font=tag_font)
            y += tag_font_size + int(tag_font_size * 0.3)

        # Brand mark at bottom
        brand_font = _load_font(max(28, w // 40), bold=True)
        brand = "LEGACY COMMERCE"
        bbox = draw.textbbox((0, 0), brand, font=brand_font)
        bx = (w - (bbox[2] - bbox[0])) // 2
        draw.text((bx, h - margin - 60), brand, fill=p["accent"], font=brand_font)

    def _draw_mug_layout(self, draw, name, tagline, w, h, p):
        """Wide landscape layout for mug wrap designs."""
        margin = 40
        inner_w = w - margin * 2

        # Full-width accent stripe at top
        draw.rectangle([0, 0, w, h // 6], fill=p["accent"])

        # Product name centered in middle band
        name_upper = name.upper()
        name_font_size = h // 3
        name_font = _load_font(name_font_size, bold=True)

        while name_font_size > 40:
            name_font = _load_font(name_font_size, bold=True)
            lines = _wrap_text(draw, name_upper, name_font, inner_w)
            if len(lines) == 1:
                break
            name_font_size -= 8

        name_lines = _wrap_text(draw, name_upper, name_font, inner_w)
        line_h = name_font_size + 10
        y = (h - line_h * len(name_lines)) // 2

        for line in name_lines:
            bbox = draw.textbbox((0, 0), line, font=name_font)
            x = (w - (bbox[2] - bbox[0])) // 2
            draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=name_font)
            draw.text((x, y), line, fill=p["text"], font=name_font)
            y += line_h

        # Tagline below name
        tag_font = _load_font(h // 8, bold=False)
        tag_lines = _wrap_text(draw, tagline, tag_font, inner_w)
        y += 10
        for line in tag_lines:
            bbox = draw.textbbox((0, 0), line, font=tag_font)
            x = (w - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, fill=p["sub"], font=tag_font)
            y += h // 7

        # Accent stripe at bottom
        draw.rectangle([0, h - h // 6, w, h], fill=p["accent"])

        # Brand mark in bottom stripe
        brand_font = _load_font(max(24, h // 8), bold=True)
        brand = "LEGACY COMMERCE"
        bbox = draw.textbbox((0, 0), brand, font=brand_font)
        bx = (w - (bbox[2] - bbox[0])) // 2
        by = h - h // 6 + (h // 6 - (bbox[3] - bbox[1])) // 2
        draw.text((bx, by), brand, fill=p["bg"], font=brand_font)
