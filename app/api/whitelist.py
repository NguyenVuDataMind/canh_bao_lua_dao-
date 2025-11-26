from datetime import date
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps.db import CurrentAsyncSession
from app.deps.users import CurrentUser
from app.models.white_list_url import WhiteListURL
from app.models.blacklist_url import BlackListURL
from app.schemas.whitelist import (
    WhiteListURLCreate,
    WhiteListURLOut,
    WhiteListURLUpdate,
    WhitelistCheckRequest,
    WhitelistCheckResponse,
    URLWhitelistMatchResult,
)
from app.services.url_whitelist import WhitelistService
from app.services.url_normalizer import URLNormalizer

router = APIRouter(prefix="/whitelist", tags=["whitelist"])


def _ensure_admin(user: CurrentUser):
    if user.role != "admin" and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thao tác whitelist",
        )


@router.post("/check", response_model=WhitelistCheckResponse)
async def check_urls(
    payload: WhitelistCheckRequest,
    session: CurrentAsyncSession,
) -> WhitelistCheckResponse:
    """Check URLs: whitelist trước, sau đó blacklist, cuối cùng là warning"""
    normalizer = URLNormalizer()
    results = []
    
    for url in payload.urls:
        normalized = normalizer.normalize(url)
        if not normalized:
            results.append(URLWhitelistMatchResult(
                original_url=url,
                normalized_url="",
                is_trusted=False,
                match_type=None,
                whitelist_entry_id=None,
                matched_pattern=None,
                reason="URL không hợp lệ"
            ))
            continue
        
        # Extract domain
        domain = normalized.split("/")[0]
        
        # 1. Check whitelist trước
        whitelist_result = await session.execute(
            select(WhiteListURL).where(WhiteListURL.domain == domain)
        )
        whitelist_entry = whitelist_result.scalar_one_or_none()
        
        if whitelist_entry:
            results.append(URLWhitelistMatchResult(
                original_url=url,
                normalized_url=normalized,
                is_trusted=True,
                match_type="whitelist",
                whitelist_entry_id=whitelist_entry.id,
                matched_pattern=domain,
                reason="✅ URL này an toàn (có trong whitelist)"
            ))
            continue
        
        # 2. Check blacklist
        blacklist_result = await session.execute(
            select(BlackListURL).where(BlackListURL.domain == domain)
        )
        blacklist_entry = blacklist_result.scalar_one_or_none()
        
        if blacklist_entry:
            results.append(URLWhitelistMatchResult(
                original_url=url,
                normalized_url=normalized,
                is_trusted=False,
                match_type="blacklist",
                whitelist_entry_id=blacklist_entry.id,
                matched_pattern=domain,
                reason="⚠️ URL này đã bị báo cáo là lừa đảo"
            ))
            continue
        
        # 3. Không có ở cả 2
        results.append(URLWhitelistMatchResult(
            original_url=url,
            normalized_url=normalized,
            is_trusted=False,
            match_type="unknown",
            whitelist_entry_id=None,
            matched_pattern=None,
            reason="⚠️ URL này chưa có trong hệ thống, hãy cẩn thận vì chưa được xác nhận"
        ))
    
    return WhitelistCheckResponse(results=results)


@router.get("/urls", response_model=list[WhiteListURLOut])
async def list_whitelist_urls(
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    stmt = select(WhiteListURL).order_by(WhiteListURL.id.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/urls", response_model=WhiteListURLOut, status_code=status.HTTP_201_CREATED)
async def create_whitelist_url(
    payload: WhiteListURLCreate,
    session: CurrentAsyncSession,
):
    """Báo cáo URL đáng ngờ - không yêu cầu đăng nhập"""
    # Kiểm tra domain đã tồn tại chưa
    existing = await session.execute(
        select(WhiteListURL).where(WhiteListURL.domain == payload.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain đã tồn tại trong whitelist",
        )
    
    today = date.today()
    entry = WhiteListURL(
        domain=payload.domain,
        company=payload.company,
        source=payload.source or "user-report",
        first_seen=today,
        last_seen=today,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.patch("/urls/{entry_id}", response_model=WhiteListURLOut)
async def update_whitelist_url(
    entry_id: int,
    payload: WhiteListURLUpdate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    entry = await session.get(WhiteListURL, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Whitelist URL không tồn tại")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    
    # Cập nhật last_seen khi có thay đổi
    entry.last_seen = date.today()
    
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/urls/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_whitelist_url(
    entry_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    entry = await session.get(WhiteListURL, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Whitelist URL không tồn tại")

    await session.delete(entry)
    await session.commit()
