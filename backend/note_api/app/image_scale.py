"""画像パーツの表示倍率"""

MIN_IMAGE_SCALE = 0.25
MAX_IMAGE_SCALE = 4.0
DEFAULT_IMAGE_SCALE = 1.0


def resolve_part_image_scale(ptype: str, scale: float | None, existing: float = DEFAULT_IMAGE_SCALE) -> float:
    if ptype not in ("jpeg", "png"):
        return DEFAULT_IMAGE_SCALE
    if scale is None:
        return _clamp_scale(existing)
    return _clamp_scale(scale)


def _clamp_scale(scale: float) -> float:
    try:
        value = float(scale)
    except (TypeError, ValueError):
        return DEFAULT_IMAGE_SCALE
    if not (value == value):  # NaN
        return DEFAULT_IMAGE_SCALE
    return max(MIN_IMAGE_SCALE, min(MAX_IMAGE_SCALE, value))
