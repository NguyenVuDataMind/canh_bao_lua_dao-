from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.white_list_url import WhiteListURL
from app.schemas.whitelist import URLWhitelistMatchResult
from app.services.url_normalizer import URLNormalizer


@dataclass
class _Match:
    entry: Optional[WhiteListURL]
    reason: Optional[str] = None


class WhitelistService:
    def __init__(
        self,
        session: AsyncSession,
        normalizer: Optional[URLNormalizer] = None,
    ):
        self.session = session
        self.normalizer = normalizer or URLNormalizer()

    async def check_urls(self, urls: Sequence[str]) -> List[URLWhitelistMatchResult]:
        entries = await self._get_whitelist_entries()
        results: List[URLWhitelistMatchResult] = []

        for url in urls:
            normalized = self.normalizer.normalize(url)
            if not normalized:
                results.append(
                    URLWhitelistMatchResult(
                        original_url=url,
                        normalized_url="",
                        is_trusted=False,
                        reason="URL không hợp lệ",
                    )
                )
                continue

            match = self._match(normalized, entries)
            results.append(
                URLWhitelistMatchResult(
                    original_url=url,
                    normalized_url=normalized,
                    is_trusted=match.entry is not None,
                    match_type=None,  # Không còn match_type nữa
                    whitelist_entry_id=match.entry.id if match.entry else None,
                    matched_pattern=match.entry.domain if match.entry else None,
                    reason=match.reason,
                )
            )
        return results

    async def _get_whitelist_entries(self) -> Sequence[WhiteListURL]:
        """Lấy tất cả domain từ bảng white_listURL"""
        stmt = select(WhiteListURL)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def _match(self, normalized: str, entries: Sequence[WhiteListURL]) -> _Match:
        """So sánh URL đã normalize với danh sách domain trong whitelist"""
        if not normalized:
            return _Match(entry=None, reason="Không thể normalize URL")

        host, path, query = self._split_normalized(normalized)
        
        # Normalize hostname để so sánh
        normalized_host = host.lower().strip()
        if normalized_host.startswith("www."):
            normalized_host = normalized_host[4:]
        
        # So sánh với từng domain trong whitelist
        for entry in entries:
            normalized_domain = entry.domain.lower().strip()
            if normalized_domain.startswith("www."):
                normalized_domain = normalized_domain[4:]
            
            # Exact match: domain khớp chính xác
            if normalized_host == normalized_domain:
                return _Match(entry=entry, reason="Khớp với domain trong whitelist")
            
            # Subdomain match: ví dụ sub.example.com khớp với example.com
            if normalized_host.endswith(f".{normalized_domain}"):
                return _Match(entry=entry, reason="Khớp với domain trong whitelist (subdomain)")
        
        return _Match(entry=None, reason="Không khớp whitelist")

    def _split_normalized(self, normalized: str) -> tuple[str, str, Optional[str]]:
        """Tách URL đã normalize thành host, path, query"""
        host, sep, rest = normalized.partition("/")
        if not sep:
            return normalized, "/", None

        if not rest:
            return host, "/", None

        if rest.startswith("?"):
            return host, "/", rest[1:] or None

        if "?" in rest:
            path_part, _, query = rest.partition("?")
            return host, f"/{path_part}", query or None

        return host, f"/{rest}", None
