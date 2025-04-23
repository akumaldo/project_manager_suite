from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PVBBase(BaseModel):
    vision: Optional[str] = Field(None, max_length=1000)
    target_customers: Optional[str] = Field(None, max_length=1000)
    customer_needs: Optional[str] = Field(None, max_length=1000)
    product_features: Optional[str] = Field(None, max_length=1000)
    business_goals: Optional[str] = Field(None, max_length=1000)


class PVBCreate(PVBBase):
    project_id: str


class PVB(PVBBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PVBUpdate(PVBBase):
    pass 