"""チェックリストパーツのサービス層。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from note_api.app.models import Checklist, ChecklistCategory, ChecklistItem, Part
from note_api.app.schemas import (
    ChecklistCategoryItem,
    ChecklistGetResponse,
    ChecklistItemItem,
    ChecklistMutationResponse,
    ResultResponse,
)

UNNAMED_CATEGORY_NAME = ""


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def create_checklist_for_part(db: Session, aid: int) -> Checklist:
    row = Checklist(aid=aid, title="")
    db.add(row)
    db.flush()
    return row


def validate_checklist_part_data(db: Session, aid: int, data: str) -> ResultResponse | None:
    if not data.strip().isdigit():
        return _fail("checklist パーツの data には checklist ID を指定してください")
    checklist_id = int(data.strip())
    row = db.scalar(
        select(Checklist).where(Checklist.id == checklist_id, Checklist.aid == aid)
    )
    if row is None:
        return _fail("指定されたチェックリストが見つかりません")
    return None


def _get_checklist_or_none(db: Session, aid: int, checklist_id: int) -> Checklist | None:
    return db.scalar(
        select(Checklist).where(Checklist.id == checklist_id, Checklist.aid == aid)
    )


def _alive_categories(db: Session, checklist_id: int) -> list[ChecklistCategory]:
    rows = db.scalars(
        select(ChecklistCategory)
        .where(
            ChecklistCategory.checklist_id == checklist_id,
            ChecklistCategory.is_deleted.is_(False),
        )
        .order_by(ChecklistCategory.dorder, ChecklistCategory.id)
    ).all()
    return list(rows)


def _alive_items(db: Session, checklist_id: int) -> list[ChecklistItem]:
    rows = db.scalars(
        select(ChecklistItem)
        .where(
            ChecklistItem.checklist_id == checklist_id,
            ChecklistItem.is_deleted.is_(False),
        )
        .order_by(ChecklistItem.dorder, ChecklistItem.id)
    ).all()
    return list(rows)


def _build_response(db: Session, checklist: Checklist) -> ChecklistMutationResponse:
    categories = _alive_categories(db, checklist.id)
    items = _alive_items(db, checklist.id)
    items_by_cat: dict[int, list[ChecklistItem]] = {}
    for item in items:
        items_by_cat.setdefault(item.category_id, []).append(item)

    category_items: list[ChecklistCategoryItem] = []
    for cat in categories:
        cat_items = items_by_cat.get(cat.id, [])
        category_items.append(
            ChecklistCategoryItem(
                id=cat.id,
                name=cat.name,
                is_unnamed=cat.name == UNNAMED_CATEGORY_NAME,
                dorder=cat.dorder,
                items=[
                    ChecklistItemItem(
                        id=item.id,
                        title=item.title,
                        is_checked=item.is_checked,
                        dorder=item.dorder,
                    )
                    for item in cat_items
                ],
            )
        )

    return ChecklistMutationResponse(
        checklist_id=checklist.id,
        title=checklist.title,
        categories=category_items,
    )


def get_checklist(
    db: Session, aid: int, checklist_id: int
) -> ChecklistGetResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    mutation = _build_response(db, checklist)
    return ChecklistGetResponse(
        checklist_id=mutation.checklist_id,
        title=mutation.title,
        categories=mutation.categories,
    )


def update_checklist_title(
    db: Session, aid: int, checklist_id: int, title: str
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    checklist.title = title
    db.commit()
    return _build_response(db, checklist)


def _next_category_dorder(db: Session, checklist_id: int) -> int:
    cats = _alive_categories(db, checklist_id)
    if not cats:
        return 0
    return max(c.dorder for c in cats) + 1


def _next_item_dorder(db: Session, category_id: int) -> int:
    rows = db.scalars(
        select(ChecklistItem).where(
            ChecklistItem.category_id == category_id,
            ChecklistItem.is_deleted.is_(False),
        )
    ).all()
    if not rows:
        return 0
    return max(r.dorder for r in rows) + 1


def _find_alive_category(
    db: Session, checklist_id: int, category_id: int
) -> ChecklistCategory | None:
    return db.scalar(
        select(ChecklistCategory).where(
            ChecklistCategory.id == category_id,
            ChecklistCategory.checklist_id == checklist_id,
            ChecklistCategory.is_deleted.is_(False),
        )
    )


def _find_alive_item(
    db: Session, checklist_id: int, item_id: int
) -> ChecklistItem | None:
    return db.scalar(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id,
            ChecklistItem.checklist_id == checklist_id,
            ChecklistItem.is_deleted.is_(False),
        )
    )


def _get_or_create_unnamed_category(
    db: Session, checklist_id: int
) -> ChecklistCategory:
    existing = db.scalar(
        select(ChecklistCategory).where(
            ChecklistCategory.checklist_id == checklist_id,
            ChecklistCategory.name == UNNAMED_CATEGORY_NAME,
            ChecklistCategory.is_deleted.is_(False),
        )
    )
    if existing is not None:
        return existing
    cat = ChecklistCategory(
        checklist_id=checklist_id,
        name=UNNAMED_CATEGORY_NAME,
        dorder=_next_category_dorder(db, checklist_id),
        is_deleted=False,
    )
    db.add(cat)
    db.flush()
    return cat


def _name_taken(
    db: Session, checklist_id: int, name: str, *, exclude_id: int | None = None
) -> bool:
    q = select(ChecklistCategory).where(
        ChecklistCategory.checklist_id == checklist_id,
        ChecklistCategory.name == name,
        ChecklistCategory.is_deleted.is_(False),
    )
    if exclude_id is not None:
        q = q.where(ChecklistCategory.id != exclude_id)
    return db.scalar(q) is not None


def create_category(
    db: Session, aid: int, checklist_id: int, name: str
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")

    trimmed = name.strip()
    if not trimmed:
        return _fail("カテゴリ名を入力してください")
    if _name_taken(db, checklist_id, trimmed):
        return _fail("同じ名前のカテゴリが既に存在します")

    cat = ChecklistCategory(
        checklist_id=checklist_id,
        name=trimmed,
        dorder=_next_category_dorder(db, checklist_id),
        is_deleted=False,
    )
    db.add(cat)
    db.commit()
    return _build_response(db, checklist)


def update_category(
    db: Session, aid: int, checklist_id: int, category_id: int, name: str
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    cat = _find_alive_category(db, checklist_id, category_id)
    if cat is None:
        return _fail("指定されたカテゴリが見つかりません")
    if cat.name == UNNAMED_CATEGORY_NAME:
        return _fail("無名カテゴリの名称は変更できません")

    trimmed = name.strip()
    if not trimmed:
        return _fail("カテゴリ名を入力してください")
    if _name_taken(db, checklist_id, trimmed, exclude_id=category_id):
        return _fail("同じ名前のカテゴリが既に存在します")

    cat.name = trimmed
    db.commit()
    return _build_response(db, checklist)


def delete_category(
    db: Session, aid: int, checklist_id: int, category_id: int
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    cat = _find_alive_category(db, checklist_id, category_id)
    if cat is None:
        return _fail("指定されたカテゴリが見つかりません")

    cat.is_deleted = True
    items = db.scalars(
        select(ChecklistItem).where(
            ChecklistItem.category_id == category_id,
            ChecklistItem.is_deleted.is_(False),
        )
    ).all()
    for item in items:
        item.is_deleted = True
    db.commit()
    return _build_response(db, checklist)


def reorder_categories(
    db: Session, aid: int, checklist_id: int, ordered_ids: list[int]
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    cats = _alive_categories(db, checklist_id)
    alive_ids = {c.id for c in cats}
    if set(ordered_ids) != alive_ids or len(ordered_ids) != len(alive_ids):
        return _fail("カテゴリの並び替え指定が不正です")

    by_id = {c.id: c for c in cats}
    for index, cat_id in enumerate(ordered_ids):
        by_id[cat_id].dorder = index
    db.commit()
    return _build_response(db, checklist)


def create_item(
    db: Session,
    aid: int,
    checklist_id: int,
    category_id: int | None,
    title: str,
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")

    if category_id is None:
        cat = _get_or_create_unnamed_category(db, checklist_id)
    else:
        cat = _find_alive_category(db, checklist_id, category_id)
        if cat is None:
            return _fail("指定されたカテゴリが見つかりません")

    item = ChecklistItem(
        checklist_id=checklist_id,
        category_id=cat.id,
        title=title,
        is_checked=False,
        dorder=_next_item_dorder(db, cat.id),
        is_deleted=False,
    )
    db.add(item)
    db.commit()
    return _build_response(db, checklist)


def update_item(
    db: Session,
    aid: int,
    checklist_id: int,
    item_id: int,
    title: str | None,
    is_checked: bool | None,
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    item = _find_alive_item(db, checklist_id, item_id)
    if item is None:
        return _fail("指定されたチェック項目が見つかりません")

    if title is not None:
        item.title = title
    if is_checked is not None:
        item.is_checked = is_checked
    db.commit()
    return _build_response(db, checklist)


def delete_item(
    db: Session, aid: int, checklist_id: int, item_id: int
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    item = _find_alive_item(db, checklist_id, item_id)
    if item is None:
        return _fail("指定されたチェック項目が見つかりません")

    item.is_deleted = True
    db.commit()
    return _build_response(db, checklist)


def _reindex_category_items(db: Session, category_id: int) -> None:
    rows = list(
        db.scalars(
            select(ChecklistItem)
            .where(
                ChecklistItem.category_id == category_id,
                ChecklistItem.is_deleted.is_(False),
            )
            .order_by(ChecklistItem.dorder, ChecklistItem.id)
        ).all()
    )
    for index, row in enumerate(rows):
        row.dorder = index


def move_item(
    db: Session,
    aid: int,
    checklist_id: int,
    item_id: int,
    to_category_id: int,
    to_index: int,
) -> ChecklistMutationResponse | ResultResponse:
    checklist = _get_checklist_or_none(db, aid, checklist_id)
    if checklist is None:
        return _fail("指定されたチェックリストが見つかりません")
    item = _find_alive_item(db, checklist_id, item_id)
    if item is None:
        return _fail("指定されたチェック項目が見つかりません")
    dest = _find_alive_category(db, checklist_id, to_category_id)
    if dest is None:
        return _fail("移動先のカテゴリが見つかりません")
    if to_index < 0:
        return _fail("挿入位置が不正です")

    source_category_id = item.category_id
    dest_items = [
        row
        for row in db.scalars(
            select(ChecklistItem)
            .where(
                ChecklistItem.category_id == to_category_id,
                ChecklistItem.is_deleted.is_(False),
            )
            .order_by(ChecklistItem.dorder, ChecklistItem.id)
        ).all()
        if row.id != item_id
    ]
    insert_at = min(to_index, len(dest_items))
    dest_items.insert(insert_at, item)
    item.category_id = to_category_id
    for index, row in enumerate(dest_items):
        row.dorder = index

    if source_category_id != to_category_id:
        _reindex_category_items(db, source_category_id)

    db.commit()
    return _build_response(db, checklist)


def delete_checklist_for_part(db: Session, aid: int, part: Part) -> None:
    if part.ptype != "checklist" or not part.data.strip().isdigit():
        return
    checklist_id = int(part.data.strip())
    row = _get_checklist_or_none(db, aid, checklist_id)
    if row is not None:
        db.delete(row)
