from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from note_api.app.action_plan import validate_action_plan_data
from note_api.app.config import get_settings
from note_api.app.models import File, Folder, Part, PartRevision
from note_api.app.schemas import (
    BelongInfo,
    FileGetResponse,
    FileItem,
    FolderItem,
    ItemsListResponse,
    ParentInfo,
    PartInfo,
    PartRevisionGetResponse,
    PartRevisionSummary,
    ResultResponse,
)

VERSIONED_PART_TYPES = frozenset({"jpeg", "png", "binary"})
settings = get_settings()


def _fail(reason: str) -> ResultResponse:
    return ResultResponse(result=False, reason=reason)


def _ok() -> ResultResponse:
    return ResultResponse(result=True, reason=None)


def _is_versioned_part_type(ptype: str) -> bool:
    return ptype in VERSIONED_PART_TYPES


def _validate_data_for_type(ptype: str, data: str) -> ResultResponse | None:
    if ptype == "action":
        return validate_action_plan_data(data)
    return None


def _validate_filename_for_type(ptype: str, filename: str) -> ResultResponse | None:
    if _is_versioned_part_type(ptype) and not filename.strip():
        return _fail("jpeg / png / binary には filename が必要です")
    return None


def _load_part_revisions(db: Session, parts_id: int) -> list[PartRevisionSummary]:
    rows = db.scalars(
        select(PartRevision)
        .where(PartRevision.parts_id == parts_id)
        .order_by(PartRevision.revision_number.desc())
    ).all()
    return [
        PartRevisionSummary(
            id=r.id,
            revision_number=r.revision_number,
            filename=r.filename,
            ptype=r.ptype,
            created_at=r.created_at.isoformat(sep=" ", timespec="seconds"),
        )
        for r in rows
    ]


def _save_part_revision(db: Session, aid: int, part: Part) -> None:
    max_number = db.scalar(
        select(func.coalesce(func.max(PartRevision.revision_number), 0)).where(
            PartRevision.parts_id == part.id
        )
    )
    revision = PartRevision(
        aid=aid,
        parts_id=part.id,
        revision_number=(max_number or 0) + 1,
        filename=part.filename,
        ptype=part.ptype,
        data=part.data,
        created_at=datetime.now(),
    )
    db.add(revision)
    db.flush()
    _prune_part_revisions(db, part.id)


def _prune_part_revisions(db: Session, parts_id: int) -> None:
    max_keep = settings.parts_max_revisions
    if max_keep <= 0:
        db.execute(delete(PartRevision).where(PartRevision.parts_id == parts_id))
        return

    keep_ids = db.scalars(
        select(PartRevision.id)
        .where(PartRevision.parts_id == parts_id)
        .order_by(PartRevision.revision_number.desc())
        .limit(max_keep)
    ).all()
    if not keep_ids:
        return
    db.execute(
        delete(PartRevision).where(
            PartRevision.parts_id == parts_id,
            PartRevision.id.not_in(keep_ids),
        )
    )


def get_folder_or_none(db: Session, aid: int, folder_id: int) -> Folder | None:
    return db.scalar(select(Folder).where(Folder.id == folder_id, Folder.aid == aid))


def get_active_folder(db: Session, aid: int, folder_id: int) -> Folder | None:
    return db.scalar(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.aid == aid,
            Folder.deleted_number == 0,
        )
    )


def _build_folder_maps(
    db: Session, aid: int
) -> tuple[dict[int, int], dict[int, int | None]]:
    folders = db.scalars(select(Folder).where(Folder.aid == aid)).all()
    deleted_map = {f.id: f.deleted_number for f in folders}
    parent_map = {f.id: f.parent for f in folders}
    return deleted_map, parent_map


def _is_ancestor_deleted(
    folder_id: int | None,
    deleted_map: dict[int, int],
    parent_map: dict[int, int | None],
) -> bool:
    current = folder_id
    visited: set[int] = set()
    while current is not None:
        if current in visited:
            return False
        visited.add(current)
        if deleted_map.get(current, 0) > 0:
            return True
        current = parent_map.get(current)
    return False


def _folder_is_del(
    folder: Folder,
    deleted_map: dict[int, int],
    parent_map: dict[int, int | None],
) -> bool:
    return folder.deleted_number > 0 or _is_ancestor_deleted(
        folder.parent, deleted_map, parent_map
    )


def _file_is_del(
    file_row: File,
    deleted_map: dict[int, int],
    parent_map: dict[int, int | None],
) -> bool:
    return file_row.deleted_number > 0 or _is_ancestor_deleted(
        file_row.belong, deleted_map, parent_map
    )


def _ensure_folder_dorder_on_undelete(db: Session, aid: int, folder: Folder) -> None:
    conflict = db.scalar(
        select(Folder.id).where(
            Folder.aid == aid,
            Folder.parent == folder.parent,
            Folder.dorder == folder.dorder,
            Folder.id != folder.id,
        )
    )
    if conflict is not None:
        folder.dorder = _next_folder_dorder(db, aid, folder.parent)


def _ensure_file_dorder_on_undelete(db: Session, aid: int, file_row: File) -> None:
    conflict = db.scalar(
        select(File.id).where(
            File.aid == aid,
            File.belong == file_row.belong,
            File.dorder == file_row.dorder,
            File.id != file_row.id,
        )
    )
    if conflict is not None:
        file_row.dorder = _next_file_dorder(db, aid, file_row.belong)


def list_items(
    db: Session,
    aid: int,
    folder_id: int | None,
    include_deleted: bool,
) -> ItemsListResponse | ResultResponse:
    if folder_id is not None:
        parent_folder = get_folder_or_none(db, aid, folder_id)
        if parent_folder is None:
            return _fail("指定されたフォルダが見つかりません")
        parent = ParentInfo(id=parent_folder.id, name=parent_folder.name)
    else:
        parent = ParentInfo(id=None, name=None)

    deleted_map, parent_map = _build_folder_maps(db, aid)

    folders = db.scalars(
        select(Folder)
        .where(Folder.aid == aid, Folder.parent == folder_id)
        .order_by(Folder.dorder)
    ).all()

    files: list[File] = []
    if folder_id is not None:
        files = list(
            db.scalars(
                select(File)
                .where(File.aid == aid, File.belong == folder_id)
                .order_by(File.dorder)
            ).all()
        )

    folder_items: list[FolderItem] = []
    for f in folders:
        is_del = _folder_is_del(f, deleted_map, parent_map)
        if include_deleted or not is_del:
            folder_items.append(
                FolderItem(id=f.id, dorder=f.dorder, name=f.name, is_del=is_del)
            )

    file_items: list[FileItem] = []
    for f in files:
        is_del = _file_is_del(f, deleted_map, parent_map)
        if include_deleted or not is_del:
            file_items.append(
                FileItem(id=f.id, dorder=f.dorder, title=f.title, is_del=is_del)
            )

    return ItemsListResponse(parent=parent, folder=folder_items, file=file_items)


def get_file_detail(
    db: Session,
    aid: int,
    file_id: int,
    include_deleted: bool = False,
) -> FileGetResponse | ResultResponse:
    file_row = db.scalar(select(File).where(File.id == file_id, File.aid == aid))
    if file_row is None:
        return _fail("指定されたファイルが見つかりません")

    folder_row = get_folder_or_none(db, aid, file_row.belong)
    if folder_row is None:
        return _fail("所属フォルダが見つかりません")

    parts_q = select(Part).where(Part.file == file_id, Part.aid == aid)
    if not include_deleted:
        parts_q = parts_q.where(Part.is_deleted.is_(False))
    parts = db.scalars(parts_q.order_by(Part.dorder)).all()

    return FileGetResponse(
        id=file_row.id,
        belong=BelongInfo(id=folder_row.id, name=folder_row.name),
        title=file_row.title,
        parts=[
            PartInfo(
                id=p.id,
                dorder=p.dorder,
                ptype=p.ptype,
                data=p.data,
                filename=p.filename,
                is_del=p.is_deleted,
                revisions=_load_part_revisions(db, p.id) if _is_versioned_part_type(p.ptype) else [],
            )
            for p in parts
        ],
    )


def _next_folder_dorder(db: Session, aid: int, parent_id: int | None) -> int:
    max_dorder = db.scalar(
        select(func.coalesce(func.max(Folder.dorder), 0)).where(
            Folder.aid == aid, Folder.parent == parent_id
        )
    )
    return (max_dorder or 0) + 1


def _next_file_dorder(db: Session, aid: int, folder_id: int) -> int:
    max_dorder = db.scalar(
        select(func.coalesce(func.max(File.dorder), 0)).where(
            File.aid == aid, File.belong == folder_id
        )
    )
    return (max_dorder or 0) + 1


def _next_part_dorder(db: Session, aid: int, file_id: int) -> int:
    max_dorder = db.scalar(
        select(func.coalesce(func.max(Part.dorder), 0)).where(
            Part.aid == aid, Part.file == file_id
        )
    )
    return (max_dorder or 0) + 1


def create_folder(db: Session, aid: int, parent_id: int | None, name: str) -> ResultResponse:
    if parent_id is not None:
        parent = get_active_folder(db, aid, parent_id)
        if parent is None:
            return _fail("親フォルダが見つかりません")

    exists = db.scalar(
        select(Folder.id).where(
            Folder.aid == aid,
            Folder.parent == parent_id,
            Folder.deleted_number == 0,
            Folder.name == name,
        )
    )
    if exists is not None:
        return _fail("同名のフォルダが既に存在します")

    folder = Folder(
        aid=aid,
        parent=parent_id,
        name=name,
        dorder=_next_folder_dorder(db, aid, parent_id),
        deleted_number=0,
    )
    db.add(folder)
    db.commit()
    return _ok()


def delete_folder(db: Session, aid: int, folder_id: int) -> ResultResponse:
    folder = db.scalar(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.aid == aid,
            Folder.deleted_number == 0,
        )
    )
    if folder is None:
        return _fail("指定されたフォルダが見つかりません")

    max_deleted = db.scalar(
        select(func.coalesce(func.max(Folder.deleted_number), 0)).where(
            Folder.aid == aid,
            Folder.parent == folder.parent,
            Folder.name == folder.name,
        )
    )
    folder.deleted_number = (max_deleted or 0) + 1
    db.commit()
    return _ok()


def undelete_folder(db: Session, aid: int, folder_id: int) -> ResultResponse:
    folder = db.scalar(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.aid == aid,
            Folder.deleted_number > 0,
        )
    )
    if folder is None:
        return _fail("指定された削除済みフォルダが見つかりません")

    conflict = db.scalar(
        select(Folder.id).where(
            Folder.aid == aid,
            Folder.parent == folder.parent,
            Folder.name == folder.name,
            Folder.deleted_number == 0,
            Folder.id != folder_id,
        )
    )
    if conflict is not None:
        return _fail("同名の有効なフォルダが既に存在します")

    folder.deleted_number = 0
    _ensure_folder_dorder_on_undelete(db, aid, folder)
    db.commit()
    return _ok()


def rename_folder(db: Session, aid: int, folder_id: int, name: str) -> ResultResponse:
    folder = db.scalar(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.aid == aid,
            Folder.deleted_number == 0,
        )
    )
    if folder is None:
        return _fail("指定されたフォルダが見つかりません")

    exists = db.scalar(
        select(Folder.id).where(
            Folder.aid == aid,
            Folder.parent == folder.parent,
            Folder.deleted_number == 0,
            Folder.name == name,
            Folder.id != folder_id,
        )
    )
    if exists is not None:
        return _fail("同名のフォルダが既に存在します")

    folder.name = name
    db.commit()
    return _ok()


def move_folder(
    db: Session,
    aid: int,
    folder_id: int,
    old_parent_id: int | None,
    new_parent_id: int | None,
) -> ResultResponse:
    folder = db.scalar(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.aid == aid,
            Folder.deleted_number == 0,
        )
    )
    if folder is None:
        return _fail("指定されたフォルダが見つかりません")

    if folder.parent != old_parent_id:
        return _fail("移動元の親フォルダが一致しません")

    if new_parent_id is not None:
        new_parent = get_active_folder(db, aid, new_parent_id)
        if new_parent is None:
            return _fail("移動先の親フォルダが見つかりません")

    exists = db.scalar(
        select(Folder.id).where(
            Folder.aid == aid,
            Folder.parent == new_parent_id,
            Folder.deleted_number == 0,
            Folder.name == folder.name,
            Folder.id != folder_id,
        )
    )
    if exists is not None:
        return _fail("移動先に同名のフォルダが既に存在します")

    folder.parent = new_parent_id
    folder.dorder = _next_folder_dorder(db, aid, new_parent_id)
    db.commit()
    return _ok()


def swap_folder_order(
    db: Session,
    aid: int,
    parent_id: int | None,
    folder_id_1: int,
    folder_id_2: int,
) -> ResultResponse:
    f1 = db.scalar(
        select(Folder).where(
            Folder.id == folder_id_1,
            Folder.aid == aid,
            Folder.parent == parent_id,
            Folder.deleted_number == 0,
        )
    )
    f2 = db.scalar(
        select(Folder).where(
            Folder.id == folder_id_2,
            Folder.aid == aid,
            Folder.parent == parent_id,
            Folder.deleted_number == 0,
        )
    )
    if f1 is None or f2 is None:
        return _fail("指定されたフォルダが見つかりません")

    d1, d2 = f1.dorder, f2.dorder
    f1.dorder = -1
    db.flush()
    f2.dorder = d1
    db.flush()
    f1.dorder = d2
    db.commit()
    return _ok()


def create_file(db: Session, aid: int, folder_id: int, title: str) -> ResultResponse:
    folder = get_active_folder(db, aid, folder_id)
    if folder is None:
        return _fail("指定されたフォルダが見つかりません")

    exists = db.scalar(
        select(File.id).where(
            File.aid == aid,
            File.belong == folder_id,
            File.deleted_number == 0,
            File.title == title,
        )
    )
    if exists is not None:
        return _fail("同名のファイルが既に存在します")

    file_row = File(
        aid=aid,
        belong=folder_id,
        title=title,
        dorder=_next_file_dorder(db, aid, folder_id),
        deleted_number=0,
    )
    db.add(file_row)
    db.commit()
    return _ok()


def delete_file(db: Session, aid: int, file_id: int) -> ResultResponse:
    file_row = db.scalar(
        select(File).where(
            File.id == file_id,
            File.aid == aid,
            File.deleted_number == 0,
        )
    )
    if file_row is None:
        return _fail("指定されたファイルが見つかりません")

    max_deleted = db.scalar(
        select(func.coalesce(func.max(File.deleted_number), 0)).where(
            File.aid == aid,
            File.belong == file_row.belong,
            File.title == file_row.title,
        )
    )
    file_row.deleted_number = (max_deleted or 0) + 1
    db.commit()
    return _ok()


def undelete_file(db: Session, aid: int, file_id: int) -> ResultResponse:
    file_row = db.scalar(
        select(File).where(
            File.id == file_id,
            File.aid == aid,
            File.deleted_number > 0,
        )
    )
    if file_row is None:
        return _fail("指定された削除済みファイルが見つかりません")

    conflict = db.scalar(
        select(File.id).where(
            File.aid == aid,
            File.belong == file_row.belong,
            File.title == file_row.title,
            File.deleted_number == 0,
            File.id != file_id,
        )
    )
    if conflict is not None:
        return _fail("同名の有効なファイルが既に存在します")

    file_row.deleted_number = 0
    _ensure_file_dorder_on_undelete(db, aid, file_row)
    db.commit()
    return _ok()


def rename_file(db: Session, aid: int, file_id: int, name: str) -> ResultResponse:
    file_row = db.scalar(
        select(File).where(
            File.id == file_id,
            File.aid == aid,
            File.deleted_number == 0,
        )
    )
    if file_row is None:
        return _fail("指定されたファイルが見つかりません")

    exists = db.scalar(
        select(File.id).where(
            File.aid == aid,
            File.belong == file_row.belong,
            File.deleted_number == 0,
            File.title == name,
            File.id != file_id,
        )
    )
    if exists is not None:
        return _fail("同名のファイルが既に存在します")

    file_row.title = name
    db.commit()
    return _ok()


def move_file(
    db: Session,
    aid: int,
    file_id: int,
    old_parent_id: int,
    new_parent_id: int,
) -> ResultResponse:
    file_row = db.scalar(
        select(File).where(
            File.id == file_id,
            File.aid == aid,
            File.deleted_number == 0,
        )
    )
    if file_row is None:
        return _fail("指定されたファイルが見つかりません")

    if file_row.belong != old_parent_id:
        return _fail("移動元のフォルダが一致しません")

    new_folder = get_active_folder(db, aid, new_parent_id)
    if new_folder is None:
        return _fail("移動先のフォルダが見つかりません")

    exists = db.scalar(
        select(File.id).where(
            File.aid == aid,
            File.belong == new_parent_id,
            File.deleted_number == 0,
            File.title == file_row.title,
            File.id != file_id,
        )
    )
    if exists is not None:
        return _fail("移動先に同名のファイルが既に存在します")

    file_row.belong = new_parent_id
    file_row.dorder = _next_file_dorder(db, aid, new_parent_id)
    db.commit()
    return _ok()


def swap_file_order(
    db: Session,
    aid: int,
    parent_id: int,
    file_id_1: int,
    file_id_2: int,
) -> ResultResponse:
    f1 = db.scalar(
        select(File).where(
            File.id == file_id_1,
            File.aid == aid,
            File.belong == parent_id,
            File.deleted_number == 0,
        )
    )
    f2 = db.scalar(
        select(File).where(
            File.id == file_id_2,
            File.aid == aid,
            File.belong == parent_id,
            File.deleted_number == 0,
        )
    )
    if f1 is None or f2 is None:
        return _fail("指定されたファイルが見つかりません")

    d1, d2 = f1.dorder, f2.dorder
    f1.dorder = -1
    db.flush()
    f2.dorder = d1
    db.flush()
    f1.dorder = d2
    db.commit()
    return _ok()


def get_part_or_none(db: Session, aid: int, parts_id: int) -> Part | None:
    return db.scalar(select(Part).where(Part.id == parts_id, Part.aid == aid))


def create_part(
    db: Session, aid: int, file_id: int, ptype: str, data: str, filename: str = ""
) -> ResultResponse:
    file_row = db.scalar(select(File).where(File.id == file_id, File.aid == aid))
    if file_row is None:
        return _fail("指定されたファイルが見つかりません")

    filename = filename.strip()
    invalid = _validate_filename_for_type(ptype, filename)
    if invalid is not None:
        return invalid

    invalid = _validate_data_for_type(ptype, data)
    if invalid is not None:
        return invalid

    part = Part(
        aid=aid,
        file=file_id,
        dorder=_next_part_dorder(db, aid, file_id),
        is_deleted=False,
        ptype=ptype,
        data=data,
        filename=filename,
    )
    db.add(part)
    db.commit()
    return _ok()


def set_part_deleted(db: Session, aid: int, parts_id: int, is_deleted: bool) -> ResultResponse:
    part = get_part_or_none(db, aid, parts_id)
    if part is None:
        return _fail("指定されたパーツが見つかりません")

    part.is_deleted = is_deleted
    db.commit()
    return _ok()


def update_part(
    db: Session,
    aid: int,
    parts_id: int,
    ptype: str,
    data: str,
    filename: str | None = None,
) -> ResultResponse:
    part = get_part_or_none(db, aid, parts_id)
    if part is None:
        return _fail("指定されたパーツが見つかりません")

    new_filename = part.filename if filename is None else filename.strip()
    invalid = _validate_filename_for_type(ptype, new_filename)
    if invalid is not None:
        return invalid

    invalid = _validate_data_for_type(ptype, data)
    if invalid is not None:
        return invalid

    content_changed = part.data != data or part.ptype != ptype or part.filename != new_filename
    if _is_versioned_part_type(part.ptype) and content_changed:
        _save_part_revision(db, aid, part)

    part.ptype = ptype
    part.data = data
    part.filename = new_filename
    db.commit()
    return _ok()


def get_part_revision(
    db: Session, aid: int, revision_id: int
) -> PartRevisionGetResponse | ResultResponse:
    row = db.scalar(
        select(PartRevision).where(PartRevision.id == revision_id, PartRevision.aid == aid)
    )
    if row is None:
        return _fail("指定された世代が見つかりません")

    return PartRevisionGetResponse(
        id=row.id,
        parts_id=row.parts_id,
        revision_number=row.revision_number,
        filename=row.filename,
        ptype=row.ptype,
        data=row.data,
        created_at=row.created_at.isoformat(sep=" ", timespec="seconds"),
    )


def swap_part_order(
    db: Session,
    aid: int,
    file_id: int,
    parts_id_1: int,
    parts_id_2: int,
) -> ResultResponse:
    p1 = db.scalar(
        select(Part).where(
            Part.id == parts_id_1,
            Part.aid == aid,
            Part.file == file_id,
            Part.is_deleted.is_(False),
        )
    )
    p2 = db.scalar(
        select(Part).where(
            Part.id == parts_id_2,
            Part.aid == aid,
            Part.file == file_id,
            Part.is_deleted.is_(False),
        )
    )
    if p1 is None or p2 is None:
        return _fail("指定されたパーツが見つかりません")

    d1, d2 = p1.dorder, p2.dorder
    p1.dorder = -1
    db.flush()
    p2.dorder = d1
    db.flush()
    p1.dorder = d2
    db.commit()
    return _ok()
