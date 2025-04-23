from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CSDCategory(str, Enum):
    CERTAINTY = "Certainty"
    SUPPOSITION = "Supposition" 
    DOUBT = "Doubt"


class CSDItemBase(BaseModel):
    category: CSDCategory
    text: str = Field(..., min_length=1, max_length=500)


class CSDItemCreate(CSDItemBase):
    project_id: str


class CSDItem(CSDItemBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CSDItemUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[CSDCategory] = None


class CSDItemList(BaseModel):
    items: List[CSDItem]
    
class CSDItemReorder(BaseModel):
    """
    Schema for reordering CSD items through drag and drop
    """
    item_ids: List[str] = Field(..., description="Ordered list of CSD item IDs after reordering")
    new_category: Optional[CSDCategory] = Field(None, description="New category if items are dragged to a different column") 