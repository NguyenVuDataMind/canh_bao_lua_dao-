from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps.db import CurrentAsyncSession
from app.deps.users import CurrentUser
from app.models.trusted_url import TrustedURL
from app.schemas.whitelist import (
    TrustedURLCreate,
    TrustedURLOut,
    TrustedURLUpdate,
    WhitelistCheckRequest,
    WhitelistCheckResponse,
)
from app.services.url_whitelist import WhitelistService

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
    service = WhitelistService(session=session)
    results = await service.check_urls(payload.urls)
    return WhitelistCheckResponse(results=results)


@router.get("/urls", response_model=list[TrustedURLOut])
async def list_trusted_urls(
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    stmt = select(TrustedURL).order_by(TrustedURL.created.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/urls", response_model=TrustedURLOut, status_code=status.HTTP_201_CREATED)
async def create_trusted_url(
    payload: TrustedURLCreate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    service = WhitelistService(session=session)
    try:
        normalized_pattern = service.normalize_for_storage(
            value=payload.value, match_type=payload.match_type
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    entry = TrustedURL(
        normalized_pattern=normalized_pattern,
        match_type=payload.match_type,
        source=payload.source,
        description=payload.description,
        raw_example=payload.value,
        is_active=payload.is_active,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.patch("/urls/{entry_id}", response_model=TrustedURLOut)
async def update_trusted_url(
    entry_id: int,
    payload: TrustedURLUpdate,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    entry = await session.get(TrustedURL, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Whitelist URL không tồn tại")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


@router.delete("/urls/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trusted_url(
    entry_id: int,
    session: CurrentAsyncSession,
    user: CurrentUser,
):
    _ensure_admin(user)
    entry = await session.get(TrustedURL, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Whitelist URL không tồn tại")

    await session.delete(entry)
    await session.commit()

