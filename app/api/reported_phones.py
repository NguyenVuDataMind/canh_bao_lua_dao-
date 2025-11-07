from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from starlette.responses import Response

from app.deps.db import CurrentAsyncSession
from app.deps.request_params import ReportedPhonesRequestParams
from app.deps.users import CurrentUser
from app.models.reported_phone import ReportedPhone
from app.schemas.reported_phone import ReportedPhone as ReportedPhoneSchema
from app.schemas.reported_phone import ReportedPhoneCreate, ReportedPhoneUpdate
from app.services.phone import normalize_phone

router = APIRouter(prefix="/reported_phones")


@router.get("/search", response_model=bool)
async def search_reported_phone(
    value: str = Query(...),
    session: CurrentAsyncSession = None,
    user: CurrentUser = None,
):
    normalized_value = normalize_phone(value)
    result = await session.execute(select(ReportedPhone.value))
    all_values = [normalize_phone(v) for v in result.scalars().all() if v]

    exists = normalized_value in all_values
    return exists


@router.get("", response_model=list[ReportedPhoneSchema])
async def get_reported_phones(
    response: Response,
    session: CurrentAsyncSession,
    request_params: ReportedPhonesRequestParams,
    user: CurrentUser,
):
    total = await session.scalar(
        select(func.count(ReportedPhone.id))
    )
    reported_phones = (
        (
            await session.execute(
                select(ReportedPhone)
                .offset(request_params.skip)
                .limit(request_params.limit)
                .order_by(request_params.order_by)
            )
        )
        .scalars()
        .all()
    )
    response.headers["Content-Range"] = (
        f"{request_params.skip}-{request_params.skip + len(reported_phones)}/{total}"
    )
    return reported_phones


@router.post("", response_model=ReportedPhoneSchema, status_code=201)
async def create_reported_phone(
    reported_phone_in: ReportedPhoneCreate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
        
    reported_phone = ReportedPhone(**reported_phone_in.model_dump())
    session.add(reported_phone)
    await session.commit()
    return reported_phone


@router.put("/{reported_phone_id}", response_model=ReportedPhoneSchema)
async def update_reported_phone(
    reported_phone_id: int,
    reported_phone_in: ReportedPhoneUpdate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
        
    reported_phone: ReportedPhone | None = await session.get(ReportedPhone, reported_phone_id)
    if not reported_phone:
        raise HTTPException(404)
    update_data = reported_phone_in.model_dump(exclude_unset=True)
    for field, value in update_data.reported_phones():
        setattr(reported_phone, field, value)
    session.add(reported_phone)
    await session.commit()
    return reported_phone


@router.get("/{reported_phone_id}", response_model=ReportedPhoneSchema)
async def get_reported_phone(
    reported_phone_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    reported_phone: ReportedPhone | None = await session.get(ReportedPhone, reported_phone_id)
    if not reported_phone:
        raise HTTPException(404)
    return reported_phone


@router.delete("/{reported_phone_id}")
async def delete_reported_phone(
    reported_phone_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
        
    reported_phone: ReportedPhone | None = await session.get(ReportedPhone, reported_phone_id)
    if not reported_phone:
        raise HTTPException(404)
    await session.delete(reported_phone)
    await session.commit()
    return {"success": True}
