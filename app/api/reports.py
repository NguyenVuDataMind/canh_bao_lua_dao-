from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy import select
from typing import Optional

from app.deps.db import CurrentAsyncSession
from app.deps.users import CurrentUser
from app.models.report import Report
from app.models.blacklist_phone import BlackListPhone
from app.models.blacklist_url import BlackListURL
from app.schemas.blacklist import ReportCreate, ReportOut
from app.services.phone import normalize_phone

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    session: CurrentAsyncSession,
    current_user: CurrentUser,
):
    """Tạo báo cáo URL hoặc SĐT đáng ngờ - yêu cầu đăng nhập"""
    report = Report(
        reported_url=payload.reported_url,
        reported_phone=payload.reported_phone,
        reported_email=payload.reported_email,
        description=payload.description,
        source=payload.source or "user-report",
        status=False,  # Chưa được duyệt
        user_id=current_user.id,  # Liên kết với user đã đăng nhập
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


@router.get("", response_model=list[ReportOut])
async def list_reports(
    session: CurrentAsyncSession,
    status_filter: Optional[bool] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Lấy danh sách báo cáo - có thể filter theo status"""
    stmt = select(Report)
    if status_filter is not None:
        stmt = stmt.where(Report.status == status_filter)
    stmt = stmt.order_by(Report.created.desc()).offset(skip).limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: int,
    session: CurrentAsyncSession,
):
    """Lấy chi tiết một báo cáo"""
    report = await session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")
    return report

