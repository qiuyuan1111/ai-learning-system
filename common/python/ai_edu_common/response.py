"""响应体构造器 —— 与 TS 版 success / error / paginated 对应。"""
from __future__ import annotations

import math
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from .enums import ErrorCodeEnum
from .ids import IdGenerator
from .models import ApiResponse, PageInfo, PaginatedData

T = TypeVar("T")


def success(data: T, request_id: Optional[str] = None) -> ApiResponse:
    """构造成功响应。"""
    return ApiResponse(
        code=ErrorCodeEnum.SUCCESS,
        message="success",
        data=data,
        requestId=request_id or IdGenerator.request_id(),
    )


def error(code: int, message: str, request_id: Optional[str] = None) -> ApiResponse:
    """构造错误响应。"""
    return ApiResponse(
        code=code,
        message=message,
        data=None,
        requestId=request_id or IdGenerator.request_id(),
    )


def paginated(items: List, page: int, page_size: int, total: int) -> PaginatedData:
    """构造分页数据，自动计算 totalPages。"""
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    return PaginatedData(
        list=items,
        pageInfo=PageInfo(
            page=page,
            pageSize=page_size,
            total=total,
            totalPages=total_pages,
        ),
    )
