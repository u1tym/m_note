import json
from typing import Any

from note_api.app.schemas import ImageMarkerItem, ResultResponse

MAX_MARKERS = 100


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def parse_markers_json(raw: str) -> list[ImageMarkerItem]:
    if not raw or raw.strip() in ("", "[]"):
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    markers: list[ImageMarkerItem] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            markers.append(ImageMarkerItem.model_validate(item))
        except Exception:
            continue
    return markers


def validate_markers(markers: list[ImageMarkerItem]) -> ResultResponse | None:
    if len(markers) > MAX_MARKERS:
        return _fail(f"マーカーは {MAX_MARKERS} 個までです")

    seen_ids: set[str] = set()
    for marker in markers:
        if marker.id in seen_ids:
            return _fail("マーカー ID が重複しています")
        seen_ids.add(marker.id)

        if not (0 <= marker.x <= 1 and 0 <= marker.y <= 1):
            return _fail("マーカー位置は 0〜1 の範囲である必要があります")

        if marker.kind == "house":
            if marker.number is not None:
                return _fail("家マーカーに番号は指定できません")
        elif marker.kind == "number":
            if marker.number is None or marker.number < 1:
                return _fail("番号マーカーには 1 以上の番号が必要です")
        else:
            return _fail("不明なマーカー種別です")

    return None


def serialize_markers(markers: list[ImageMarkerItem]) -> str:
    payload: list[dict[str, Any]] = []
    for marker in markers:
        item: dict[str, Any] = {
            "id": marker.id,
            "kind": marker.kind,
            "x": marker.x,
            "y": marker.y,
            "text": marker.text,
        }
        if marker.kind == "number":
            item["number"] = marker.number
        payload.append(item)
    return json.dumps(payload, ensure_ascii=False)


def resolve_part_markers_db(
    ptype: str,
    markers: list[ImageMarkerItem] | None,
    existing_json: str = "[]",
    *,
    reset: bool = False,
) -> tuple[str, ResultResponse | None]:
    if ptype not in ("jpeg", "png"):
        return "[]", None
    if reset:
        return "[]", None
    if markers is None:
        return existing_json or "[]", None
    invalid = validate_markers(markers)
    if invalid is not None:
        return existing_json or "[]", invalid
    return serialize_markers(markers), None


def markers_for_response(ptype: str, raw: str) -> list[ImageMarkerItem]:
    if ptype not in ("jpeg", "png"):
        return []
    return parse_markers_json(raw)
