from pydantic import BaseModel
from typing import Optional, Any


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: list[Any], total: int, page: int, size: int):
        pages = (total + size - 1) // size
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
