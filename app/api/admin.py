from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select

from app.deps.db import CurrentAsyncSession
from app.models.report import Report
from app.models.blacklist_phone import BlackListPhone
from app.models.blacklist_url import BlackListURL
from app.schemas.blacklist import BlackListPhoneOut, BlackListURLOut, ReportOut
from app.services.phone import normalize_phone
from app.services.url_normalizer import URLNormalizer

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin_password(password: str):
    """Verify admin password"""
    ADMIN_PASSWORD = "chongluadaotmdt"
    if password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu admin không đúng"
        )
    return True


@router.post("/approve-report/{report_id}/phone", response_model=BlackListPhoneOut)
async def approve_report_phone(
    report_id: int,
    session: CurrentAsyncSession,
    password: str = Query(...),
):
    """Duyệt báo cáo SĐT - chuyển vào blacklist_phone"""
    verify_admin_password(password)
    
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    if not report.reported_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Báo cáo này không có số điện thoại"
        )
    
    # Kiểm tra đã có trong blacklist chưa
    normalized_phone = normalize_phone(report.reported_phone)
    existing = await session.execute(
        select(BlackListPhone).where(BlackListPhone.value == normalized_phone)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số điện thoại đã có trong blacklist"
        )
    
    # Tạo blacklist entry
    blacklist_phone = BlackListPhone(
        value=normalized_phone,
        description=report.description,
        report_id=report_id,
    )
    session.add(blacklist_phone)
    
    # Cập nhật status report
    report.status = True
    
    await session.commit()
    await session.refresh(blacklist_phone)
    return blacklist_phone


@router.post("/approve-report/{report_id}/url", response_model=BlackListURLOut)
async def approve_report_url(
    report_id: int,
    session: CurrentAsyncSession,
    password: str = Query(...),
):
    """Duyệt báo cáo URL - chuyển vào blacklist_url"""
    verify_admin_password(password)
    
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    if not report.reported_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Báo cáo này không có URL"
        )
    
    # Extract domain từ URL
    normalizer = URLNormalizer()
    normalized = normalizer.normalize(report.reported_url)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL không hợp lệ"
        )
    
    # Lấy domain (phần trước dấu /)
    domain = normalized.split("/")[0]
    
    # Kiểm tra đã có trong blacklist chưa
    existing = await session.execute(
        select(BlackListURL).where(BlackListURL.domain == domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain đã có trong blacklist"
        )
    
    # Tạo blacklist entry
    blacklist_url = BlackListURL(
        domain=domain,
        description=report.description,
        source=report.source or "admin-approved",
        report_id=report_id,
    )
    session.add(blacklist_url)
    
    # Cập nhật status report
    report.status = True
    
    await session.commit()
    await session.refresh(blacklist_url)
    return blacklist_url


@router.get("/pending-reports", response_model=list[ReportOut])
async def get_pending_reports(
    session: CurrentAsyncSession,
    password: str = Query(...),
):
    """Lấy danh sách báo cáo chờ duyệt"""
    verify_admin_password(password)
    
    stmt = select(Report).where(Report.status.is_(False)).order_by(Report.created.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/reject-report/{report_id}")
async def reject_report(
    report_id: int,
    session: CurrentAsyncSession,
    password: str = Query(...),
):
    """Đánh dấu báo cáo là không phải lừa đảo - không đưa vào blacklist, chỉ đánh dấu đã duyệt"""
    verify_admin_password(password)
    
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    
    # Chỉ đánh dấu đã duyệt, không đưa vào blacklist
    report.status = True
    
    await session.commit()
    return {"success": True, "message": "Đã đánh dấu báo cáo là không phải lừa đảo"}

