from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Iterable, List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trusted_url import TrustedURL, WhitelistMatchType
from app.schemas.whitelist import URLWhitelistMatchResult
from app.services.url_normalizer import URLNormalizer


@dataclass
class _Match:
    entry: TrustedURL | None
    reason: str | None = None


class WhitelistService:
    def __init__(
        self,
        session: AsyncSession,
        normalizer: URLNormalizer | None = None,
    ):
        self.session = session
        self.normalizer = normalizer or URLNormalizer()

    async def check_urls(self, urls: Sequence[str]) -> List[URLWhitelistMatchResult]:
        entries = await self._get_active_entries()
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
                    match_type=match.entry.match_type if match.entry else None,
                    whitelist_entry_id=match.entry.id if match.entry else None,
                    matched_pattern=match.entry.normalized_pattern
                    if match.entry
                    else None,
                    reason=match.reason,
                )
            )
        return results

    def normalize_for_storage(
        self, value: str, match_type: WhitelistMatchType
    ) -> str:
        """
        Chuẩn hoá pattern trước khi lưu vào DB.
        """
        cleaned = value.strip()
        if match_type == WhitelistMatchType.WILDCARD:
            if "://" in cleaned or "/" in cleaned:
                normalized = self.normalizer.normalize(cleaned)
                cleaned = normalized.split("/", 1)[0] if normalized else ""
            if not cleaned:
                raise ValueError("Không thể normalize URL cho wildcard")
            cleaned = cleaned.lower()
            if cleaned.startswith("www."):
                cleaned = cleaned[4:]
            if not cleaned.startswith("*.") and "*" not in cleaned:
                cleaned = f"*.{cleaned}"
            return cleaned

        normalized = self.normalizer.normalize(cleaned)
        if not normalized:
            raise ValueError("Không thể normalize URL được cung cấp")
        if match_type == WhitelistMatchType.PREFIX:
            if "?" in normalized:
                return normalized
            if not normalized.endswith("/"):
                normalized = f"{normalized}/"
        return normalized

    async def _get_active_entries(self) -> Sequence[TrustedURL]:
        stmt = select(TrustedURL).where(TrustedURL.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def _match(self, normalized: str, entries: Iterable[TrustedURL]) -> _Match:
        if not normalized:
            return _Match(entry=None, reason="Không thể normalize URL")

        host, path, query = self._split_normalized(normalized)
        for entry in entries:
            if entry.match_type == WhitelistMatchType.EXACT:
                if normalized == entry.normalized_pattern:
                    return _Match(entry=entry)
            elif entry.match_type == WhitelistMatchType.PREFIX:
                if normalized.startswith(entry.normalized_pattern):
                    return _Match(entry=entry)
            elif entry.match_type == WhitelistMatchType.WILDCARD:
                patterns = [entry.normalized_pattern]
                if "*" not in entry.normalized_pattern:
                    patterns.append(f"*.{entry.normalized_pattern}")
                else:
                    base = entry.normalized_pattern.replace("*.", "", 1)
                    patterns.append(base)
                for pattern in patterns:
                    if fnmatch(host, pattern):
                        return _Match(entry=entry)
        return _Match(entry=None, reason="Không khớp whitelist")

    def _split_normalized(self, normalized: str) -> tuple[str, str, str | None]:
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

