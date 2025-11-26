from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, unquote

from app.core.config import settings


class URLNormalizer:
    """
    Chuẩn hoá URL để phục vụ so sánh trong whitelist.
    """

    def __init__(
        self,
        tracking_params: Optional[Iterable[str]] = None,
        keep_params: Optional[Iterable[str]] = None,
        tracking_prefixes: Optional[Iterable[str]] = None,
    ):
        self.tracking_params = {p.lower() for p in (tracking_params or settings.WHITELIST_TRACKING_PARAMS)}
        self.keep_params = {p.lower() for p in (keep_params or settings.WHITELIST_KEEP_PARAMS)}
        prefixes = tracking_prefixes or settings.WHITELIST_TRACKING_PREFIXES
        self.tracking_prefixes = tuple(p.lower() for p in prefixes)

    def normalize(self, url: str) -> str:
        """
        Chuẩn hoá URL theo bộ quy tắc:
        - Bỏ protocol, www.
        - Normalize path và query.
        - Loại bỏ tracking params, sắp xếp query theo alphabet.
        """
        if not url:
            return ""

        candidate = url.strip()
        if "://" not in candidate:
            candidate = f"http://{candidate}"

        parsed = urlsplit(candidate)
        hostname = (parsed.hostname or "").lower()
        if hostname.startswith("www."):
            hostname = hostname[4:]

        path = parsed.path or "/"
        path = unquote(path)
        if not path.startswith("/"):
            path = f"/{path}"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        if not path:
            path = "/"

        filtered_query = self._filter_query(parsed.query)
        normalized = f"{hostname}{path}"
        if filtered_query:
            normalized = f"{normalized}?{filtered_query}"
        return normalized

    def _filter_query(self, query: str) -> str:
        if not query:
            return ""

        pairs = parse_qsl(query, keep_blank_values=False)
        kept: list[tuple[str, str]] = []
        for key, value in pairs:
            key_lower = key.lower()
            if key_lower in self.tracking_params:
                continue
            if any(key_lower.startswith(prefix) for prefix in self.tracking_prefixes):
                continue
            if key_lower not in self.keep_params:
                continue
            kept.append((key_lower, value))

        if not kept:
            return ""

        kept.sort(key=lambda item: item[0])
        return urlencode(kept, doseq=True)

