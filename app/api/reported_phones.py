from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from starlette.responses import Response

from app.deps.db import CurrentAsyncSession
from app.deps.request_params import ReportedPhonesRequestParams
from app.deps.users import CurrentUser
from app.models.blacklist_phone import BlackListPhone
from app.schemas.blacklist import BlackListPhoneOut, BlackListPhoneCreate
from app.services.phone import normalize_phone

router = APIRouter(prefix="/reported_phones")


@router.get("/search")
async def search_reported_phone(
    session: CurrentAsyncSession,
    value: str = Query(...),
):
    """Tìm kiếm số điện thoại trong blacklist - không yêu cầu đăng nhập
    
    Returns:
    - {"status": "danger", "message": "Số điện thoại này đã bị báo cáo là lừa đảo"} nếu có trong blacklist
    - {"status": "warning", "message": "Số điện thoại này chưa có trong hệ thống, hãy cẩn thận"} nếu không có
    """
    normalized_value = normalize_phone(value)
    
    # Kiểm tra trong blacklist
    result = await session.execute(
        select(BlackListPhone).where(BlackListPhone.value == normalized_value)
    )
    blacklist_entry = result.scalar_one_or_none()
    
    if blacklist_entry:
        return {
            "status": "danger",
            "message": "⚠️ Số điện thoại này đã bị báo cáo là lừa đảo",
            "found": True
        }
    else:
        return {
            "status": "warning",
            "message": "⚠️ Số điện thoại này chưa có trong hệ thống, hãy cẩn thận",
            "found": False
        }


@router.get("", response_model=list[BlackListPhoneOut])
async def get_reported_phones(
    response: Response,
    session: CurrentAsyncSession,
    request_params: ReportedPhonesRequestParams,
    user: CurrentUser,
):
    total = await session.scalar(
        select(func.count(BlackListPhone.id))
    )
    reported_phones = (
        (
            await session.execute(
                select(BlackListPhone)
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


@router.post("", response_model=BlackListPhoneOut, status_code=201)
async def create_reported_phone(
    reported_phone_in: BlackListPhoneCreate,
    session: CurrentAsyncSession,
):
    """Báo cáo số điện thoại đáng ngờ - không yêu cầu đăng nhập"""
    reported_phone = BlackListPhone(**reported_phone_in.model_dump())
    session.add(reported_phone)
    await session.commit()
    await session.refresh(reported_phone)
    return reported_phone


@router.put("/{reported_phone_id}", response_model=BlackListPhoneOut)
async def update_reported_phone(
    reported_phone_id: int,
    reported_phone_in: BlackListPhoneCreate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
        
    reported_phone: Optional[BlackListPhone] = await session.get(BlackListPhone, reported_phone_id)
    if not reported_phone:
        raise HTTPException(404)
    update_data = reported_phone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reported_phone, field, value)
    session.add(reported_phone)
    await session.commit()
    return reported_phone


@router.get("/{reported_phone_id}", response_model=BlackListPhoneOut)
async def get_reported_phone(
    reported_phone_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    reported_phone: Optional[BlackListPhone] = await session.get(BlackListPhone, reported_phone_id)
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
        
    reported_phone: Optional[BlackListPhone] = await session.get(BlackListPhone, reported_phone_id)
    if not reported_phone:
        raise HTTPException(404)
    await session.delete(reported_phone)
    await session.commit()
    return {"success": True}
