"""行動予定（action）パーツの data JSON 検証。"""

from __future__ import annotations

import json
from typing import Any

from note_api.app.schemas import ResultResponse


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def _strip_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _point_is_empty(point: dict[str, Any]) -> bool:
    return not any(
        _strip_str(point.get(key))
        for key in ("place", "time", "arrive", "depart")
    )


def validate_action_plan_data(data: str) -> ResultResponse | None:
    try:
        raw = json.loads(data)
    except json.JSONDecodeError:
        return _fail("action パーツの data は有効な JSON である必要があります")

    if not isinstance(raw, dict):
        return _fail("action パーツの data は JSON オブジェクトである必要があります")

    points_raw = raw.get("points")
    legs_raw = raw.get("legs")

    if not isinstance(points_raw, list) or len(points_raw) < 1:
        return _fail("action パーツには少なくとも地点1が必要です")

    if not isinstance(legs_raw, list):
        return _fail("action パーツの legs は配列である必要があります")

    points: list[dict[str, str]] = []
    for i, item in enumerate(points_raw):
        if not isinstance(item, dict):
            return _fail(f"地点{i + 1} の形式が不正です")

        point = {
            "place": _strip_str(item.get("place")),
            "time": _strip_str(item.get("time")),
            "arrive": _strip_str(item.get("arrive")),
            "depart": _strip_str(item.get("depart")),
        }

        if i == 0:
            if not point["place"]:
                return _fail("地点1の場所は必須です")
            if not point["time"]:
                return _fail("地点1の時刻は必須です")
            points.append({"place": point["place"], "time": point["time"]})
            continue

        if _point_is_empty(item):
            continue

        normalized: dict[str, str] = {"place": point["place"]}
        if point["arrive"] or point["depart"]:
            if point["time"]:
                return _fail(f"地点{i + 1} は単一時刻と到着・出発を同時に指定できません")
            if point["arrive"]:
                normalized["arrive"] = point["arrive"]
            if point["depart"]:
                normalized["depart"] = point["depart"]
        elif point["time"]:
            normalized["time"] = point["time"]

        if not normalized.get("place") and len(normalized) == 1:
            return _fail(f"地点{i + 1} に場所または時刻を入力してください")

        points.append(normalized)

    if len(points) < 1:
        return _fail("地点1は必須です")

    if len(legs_raw) != max(0, len(points) - 1):
        return _fail("経由メモ（legs）の数は地点数 - 1 である必要があります")

    for i, leg in enumerate(legs_raw):
        if not isinstance(leg, dict):
            return _fail(f"経由{i + 1} の形式が不正です")
        memo = _strip_str(leg.get("memo"))
        if i >= len(points) - 1 and memo:
            return _fail("最後の地点より後の経由メモは指定できません")

    return None
