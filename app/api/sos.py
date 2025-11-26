from typing import Optional
from fastapi import APIRouter, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import CurrentAsyncSession
from app.deps.users import CurrentUser
from app.models.sos_request import SOSRequest
from app.schemas.sos import SOSRequestCreate, SOSRequestOut
from app.services.mail import send_sos_email

router = APIRouter(prefix="/sos", tags=["sos"])


@router.post("", response_model=SOSRequestOut, status_code=201)
async def create_sos_request(
    sos_data: SOSRequestCreate,
    request: Request,
    session: CurrentAsyncSession,
    current_user: CurrentUser,
):
    """Tạo SOS request - gửi vị trí và thông báo admin - yêu cầu đăng nhập"""
    
    # Lấy IP và User-Agent
    ip_address = None
    if request.client:
        ip_address = request.client.host
    user_agent = request.headers.get("user-agent")
    
    # Tạo SOS request
    sos_request = SOSRequest(
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
        accuracy=sos_data.accuracy,
        ip_address=ip_address,
        user_agent=user_agent,
        status="pending",
        user_id=current_user.id,  # Liên kết với user đã đăng nhập
    )
    
    session.add(sos_request)
    await session.commit()
    await session.refresh(sos_request)
    
    # Gửi email thông báo cho admin (async - không block request)
    # Kiểm tra xem có email config không
    import os
    from dotenv import load_dotenv
    load_dotenv()
    has_email_config = os.getenv("EMAIL") and os.getenv("APP_PASSWORD")
    
    try:
        send_sos_email(sos_request, test_mode=not has_email_config)
    except Exception as e:
        # Log lỗi nhưng không fail request
        print(f"Failed to send SOS email: {e}")
    
    return sos_request


@router.get("", response_model=list[SOSRequestOut])
async def get_sos_requests(
    session: CurrentAsyncSession,
    status: Optional[str] = None,
    limit: int = 50,
):
    """Lấy danh sách SOS requests (cho admin)"""
    stmt = select(SOSRequest).order_by(SOSRequest.created.desc()).limit(limit)
    
    if status:
        stmt = stmt.where(SOSRequest.status == status)
    
    result = await session.execute(stmt)
    return result.scalars().all()


@router.patch("/{sos_id}/status", response_model=SOSRequestOut)
async def update_sos_status(
    sos_id: int,
    session: CurrentAsyncSession,
    status: str = Query(...),
    notes: Optional[str] = Query(None),
):
    """Cập nhật trạng thái SOS request (cho admin)"""
    sos_request = await session.get(SOSRequest, sos_id)
    if not sos_request:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=404, detail="SOS request không tồn tại")
    
    sos_request.status = status
    if notes:
        sos_request.notes = notes
    
    await session.commit()
    await session.refresh(sos_request)
    return sos_request

