"""Pagination utilities"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Query
from math import ceil

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    page: int = 1
    limit: int = 20
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and limit"""
        return (self.page - 1) * self.limit
    
    def validate_params(self):
        """Validate pagination parameters"""
        if self.page < 1:
            self.page = 1
        if self.limit < 1:
            self.limit = 1
        if self.limit > 100:  # Max limit
            self.limit = 100


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    pages: int
    limit: int
    has_next: bool
    has_prev: bool
    
    class Config:
        from_attributes = True


def paginate(query: Query, params: PaginationParams, model: type) -> PaginatedResponse:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        params: Pagination parameters
        model: Pydantic model for items
        
    Returns:
        PaginatedResponse with items and metadata
    """
    params.validate_params()
    
    # Get total count
    total = query.count()
    
    # Calculate pages
    pages = ceil(total / params.limit) if params.limit > 0 else 0
    
    # Get items for current page
    items = query.offset(params.offset).limit(params.limit).all()
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        pages=pages,
        limit=params.limit,
        has_next=params.page < pages,
        has_prev=params.page > 1
    )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters (for infinite scroll)"""
    cursor: Optional[str] = None
    limit: int = 20
    
    def validate_params(self):
        """Validate pagination parameters"""
        if self.limit < 1:
            self.limit = 1
        if self.limit > 100:
            self.limit = 100


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response"""
    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool = False
    
    class Config:
        from_attributes = True
