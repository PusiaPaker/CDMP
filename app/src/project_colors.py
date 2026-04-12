from __future__ import annotations

import colorsys
import hashlib
from collections.abc import Iterable


UNLISTED_EVENT_COLOR = {
    "background": "#fef3c7",
    "border": "#f59e0b",
    "text": "#92400e",
}


def _hsl_to_hex(hue: float, saturation: float, lightness: float) -> str:
    red, green, blue = colorsys.hls_to_rgb(hue / 360, lightness / 100, saturation / 100)
    return "#{:02x}{:02x}{:02x}".format(
        round(red * 255),
        round(green * 255),
        round(blue * 255),
    )



def _normalize_project_ids(project_ids: Iterable[str]) -> list[str]:
    return sorted(
        {(project_id or "").strip() for project_id in project_ids if (project_id or "").strip()},
        key=lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest(),
    )


def _build_color_variant(hue: float, variant_index: int) -> dict[str, str]:
    variants = (
        {"background_saturation": 66, "background_lightness": 92, "border_saturation": 72, "border_lightness": 48, "text_saturation": 56, "text_lightness": 24},
        {"background_saturation": 58, "background_lightness": 94, "border_saturation": 68, "border_lightness": 44, "text_saturation": 48, "text_lightness": 22},
        {"background_saturation": 72, "background_lightness": 90, "border_saturation": 78, "border_lightness": 50, "text_saturation": 60, "text_lightness": 26},
        {"background_saturation": 62, "background_lightness": 91, "border_saturation": 70, "border_lightness": 46, "text_saturation": 52, "text_lightness": 23},
    )
    variant = variants[variant_index % len(variants)]
    return {
        "background": _hsl_to_hex(hue, variant["background_saturation"], variant["background_lightness"]),
        "border": _hsl_to_hex(hue, variant["border_saturation"], variant["border_lightness"]),
        "text": _hsl_to_hex(hue, variant["text_saturation"], variant["text_lightness"]),
    }


def build_project_color_map(project_ids: Iterable[str]) -> dict[str, dict[str, str]]:
    normalized_ids = _normalize_project_ids(project_ids)
    if not normalized_ids:
        return {}

    set_fingerprint = "|".join(normalized_ids)
    rotation = int(hashlib.sha256(set_fingerprint.encode("utf-8")).hexdigest()[:8], 16) % 360
    project_count = len(normalized_ids)
    step = 360 / project_count

    color_map: dict[str, dict[str, str]] = {}
    for index, project_id in enumerate(normalized_ids):
        digest = hashlib.sha256(project_id.encode("utf-8")).hexdigest()
        hue = (rotation + (index * step)) % 360
        hue += ((int(digest[8:10], 16) / 255) - 0.5) * min(step * 0.18, 6)
        variant_index = int(digest[10:12], 16) % 4
        color_map[project_id] = _build_color_variant(hue % 360, variant_index)

    return color_map


def get_project_color(project_id: str | None) -> dict[str, str]:
    normalized = (project_id or "").strip()
    if not normalized:
        return dict(UNLISTED_EVENT_COLOR)

    return build_project_color_map([normalized]).get(normalized, dict(UNLISTED_EVENT_COLOR))
