"""行動予定（action）パーツの data JSON 検証。"""

from __future__ import annotations

import json
from typing import Any

from note_api.app.schemas import ResultResponse


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def _as_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value


def _trim_end(value: Any) -> str:
    return _as_str(value).rstrip()


def _trim_time(value: Any) -> str:
    return _as_str(value).strip()


def _is_blank(value: Any) -> bool:
    return _as_str(value).strip() == ""


def _point_is_empty(point: dict[str, Any]) -> bool:
    return not any(
        not _is_blank(point.get(key))
        for key in ("place", "time", "arrive", "depart")
    )


def _normalize_point_fields(item: dict[str, Any]) -> dict[str, str]:
    return {
        "place": _trim_end(item.get("place")),
        "time": _trim_time(item.get("time")),
        "arrive": _trim_time(item.get("arrive")),
        "depart": _trim_time(item.get("depart")),
    }


def _plan_has_content(points: list[dict[str, str]], legs_raw: list[Any]) -> bool:
    if any(not _point_is_empty(p) for p in points):
        return True
    for leg in legs_raw:
        if not isinstance(leg, dict):
            continue
        if not _is_blank(_trim_end(leg.get("memo"))):
            return True
        if not _is_blank(_trim_end(leg.get("note"))):
            return True
    return False


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
        return _fail("action パーツには points 配列が1件以上必要です")

    if not isinstance(legs_raw, list):
        return _fail("action パーツの legs は配列である必要があります")

    points: list[dict[str, str]] = []
    for i, item in enumerate(points_raw):
        if not isinstance(item, dict):
            return _fail(f"地点{i + 1} の形式が不正です")

        point = _normalize_point_fields(item)

        if i == 0:
            has_later_points = any(
                not _point_is_empty(_normalize_point_fields(p))
                for p in points_raw[1:]
                if isinstance(p, dict)
            )
            if _point_is_empty(point) and not has_later_points:
                continue
            points.append({"place": point["place"], "time": point["time"]})
            continue

        if _point_is_empty(point):
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

        if _is_blank(normalized.get("place")) and len(normalized) == 1:
            return _fail(f"地点{i + 1} に場所または時刻を入力してください")

        points.append(normalized)

    if not _plan_has_content(points, legs_raw):
        return _fail("行動予定の内容を1件以上入力してください")

    if len(legs_raw) != max(0, len(points) - 1):
        return _fail("経由メモ（legs）の数は地点数 - 1 である必要があります")

    for i, leg in enumerate(legs_raw):
        if not isinstance(leg, dict):
            return _fail(f"経由{i + 1} の形式が不正です")
        memo = _trim_end(leg.get("memo"))
        note = _trim_end(leg.get("note"))
        if i >= len(points) - 1 and (not _is_blank(memo) or not _is_blank(note)):
            return _fail("最後の地点より後の経由メモは指定できません")
        if leg.get("note") is not None and not isinstance(leg.get("note"), str):
            return _fail(f"経由{i + 1} の補足メモは文字列である必要があります")

    return None
