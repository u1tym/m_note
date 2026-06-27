from fastapi import APIRouter, HTTPException

from note_api.app.deps import CurrentAid, DbSession
from note_api.app.schemas import (
    PartCreateRequest,
    PartIdRequest,
    PartRevisionGetRequest,
    PartRevisionGetResponse,
    PartSwapOrderRequest,
    PartUpdateRequest,
    ResultResponse,
)
from note_api.app.services import note_service

router = APIRouter(prefix="/parts", tags=["parts"])


@router.post("/create", response_model=ResultResponse)
def create_part(body: PartCreateRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.create_part(
        db,
        aid,
        body.file_id,
        body.ptype,
        body.data,
        body.filename,
        body.title,
        body.markers,
        body.image_scale,
    )


@router.post("/delete", response_model=ResultResponse)
def delete_part(body: PartIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.set_part_deleted(db, aid, body.parts_id, True)


@router.post("/undelete", response_model=ResultResponse)
def undelete_part(body: PartIdRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.set_part_deleted(db, aid, body.parts_id, False)


@router.post("/update", response_model=ResultResponse)
def update_part(body: PartUpdateRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.update_part(
        db,
        aid,
        body.parts_id,
        body.ptype,
        body.data,
        body.filename,
        body.title,
        body.markers,
        body.image_scale,
    )


@router.post("/revision/get", response_model=PartRevisionGetResponse)
def get_part_revision(
    body: PartRevisionGetRequest, aid: CurrentAid, db: DbSession
) -> PartRevisionGetResponse:
    result = note_service.get_part_revision(db, aid, body.revision_id)
    if isinstance(result, ResultResponse):
        raise HTTPException(status_code=404, detail=result.reason)
    return result


@router.post("/swap-order", response_model=ResultResponse)
def swap_part_order(body: PartSwapOrderRequest, aid: CurrentAid, db: DbSession) -> ResultResponse:
    return note_service.swap_part_order(
        db, aid, body.file_id, body.parts_id_1, body.parts_id_2
    )
