from fastapi import APIRouter, HTTPException

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import (
    ChecklistCategoryCreateRequest,
    ChecklistCategoryDeleteRequest,
    ChecklistCategoryReorderRequest,
    ChecklistCategoryUpdateRequest,
    ChecklistGetRequest,
    ChecklistGetResponse,
    ChecklistItemCreateRequest,
    ChecklistItemDeleteRequest,
    ChecklistItemMoveRequest,
    ChecklistItemUpdateRequest,
    ChecklistMutationResponse,
    ChecklistTitleUpdateRequest,
    ResultResponse,
)
from note_api.app.services import checklist_service

router = APIRouter(prefix="/checklist", tags=["checklist"])


def _raise_if_failed(result: ResultResponse) -> None:
    if not result.result:
        raise HTTPException(status_code=400, detail=result.reason)


@router.post("/get", response_model=ChecklistGetResponse)
def get_checklist(
    body: ChecklistGetRequest, aid: CurrentAid, db: DbSession
) -> ChecklistGetResponse:
    result = checklist_service.get_checklist(db, aid, body.checklist_id)
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/title/update", response_model=ChecklistMutationResponse)
def update_checklist_title(
    body: ChecklistTitleUpdateRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.update_checklist_title(
        db, aid, body.checklist_id, body.title
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/categories/create", response_model=ChecklistMutationResponse)
def create_category(
    body: ChecklistCategoryCreateRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.create_category(
        db, aid, body.checklist_id, body.name
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/categories/update", response_model=ChecklistMutationResponse)
def update_category(
    body: ChecklistCategoryUpdateRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.update_category(
        db, aid, body.checklist_id, body.category_id, body.name
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/categories/delete", response_model=ChecklistMutationResponse)
def delete_category(
    body: ChecklistCategoryDeleteRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.delete_category(
        db, aid, body.checklist_id, body.category_id
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/categories/reorder", response_model=ChecklistMutationResponse)
def reorder_categories(
    body: ChecklistCategoryReorderRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.reorder_categories(
        db, aid, body.checklist_id, body.ordered_ids
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/items/create", response_model=ChecklistMutationResponse)
def create_item(
    body: ChecklistItemCreateRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.create_item(
        db, aid, body.checklist_id, body.category_id, body.title
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/items/update", response_model=ChecklistMutationResponse)
def update_item(
    body: ChecklistItemUpdateRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.update_item(
        db,
        aid,
        body.checklist_id,
        body.item_id,
        body.title,
        body.is_checked,
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/items/delete", response_model=ChecklistMutationResponse)
def delete_item(
    body: ChecklistItemDeleteRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.delete_item(
        db, aid, body.checklist_id, body.item_id
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result


@router.post("/items/move", response_model=ChecklistMutationResponse)
def move_item(
    body: ChecklistItemMoveRequest, aid: CurrentAid, db: DbSession
) -> ChecklistMutationResponse:
    result = checklist_service.move_item(
        db,
        aid,
        body.checklist_id,
        body.item_id,
        body.to_category_id,
        body.to_index,
    )
    if isinstance(result, ResultResponse):
        _raise_if_failed(result)
    return result
