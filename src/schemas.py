from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field


class RegisterResponse(BaseModel):
    id: int
    username: str


class AuthorizeResponse(BaseModel):
    accessToken: str = Field(min_length=10)
    tokenType: str


class CreateItemResponse(BaseModel):
    status: str


class StatisticsSchema(BaseModel):
    likes: int
    viewCount: int
    contacts: int


class ItemSchema(BaseModel):
    id: str
    sellerId: int
    name: str
    price: Union[int, float]
    statistics: StatisticsSchema
    createdAt: Optional[str] = None
