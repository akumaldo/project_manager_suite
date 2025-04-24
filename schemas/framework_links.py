from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime


class FrameworkLinkBase(BaseModel):
    project_id: UUID4
    source_item_id: UUID4
    source_item_type: str
    target_item_id: UUID4
    target_item_type: str
    link_type: Optional[str] = None


class FrameworkLinkCreate(FrameworkLinkBase):
    pass


class FrameworkLinkUpdate(BaseModel):
    link_type: Optional[str] = None


class FrameworkLink(FrameworkLinkBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FrameworkLinkResponse(FrameworkLink):
    pass


class LinkedItemSnippet(BaseModel):
    id: UUID4
    type: str
    content: str
    name: Optional[str] = None


class LinkedItemsResponse(BaseModel):
    items: List[LinkedItemSnippet] 