from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BMCBase(BaseModel):
    key_partners: Optional[str] = Field(None, max_length=1000)
    key_activities: Optional[str] = Field(None, max_length=1000)
    key_resources: Optional[str] = Field(None, max_length=1000)
    value_propositions: Optional[str] = Field(None, max_length=1000)
    customer_relationships: Optional[str] = Field(None, max_length=1000)
    channels: Optional[str] = Field(None, max_length=1000)
    customer_segments: Optional[str] = Field(None, max_length=1000)
    cost_structure: Optional[str] = Field(None, max_length=1000)
    revenue_streams: Optional[str] = Field(None, max_length=1000)


class BMCCreate(BMCBase):
    project_id: str


class BMC(BMCBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BMCUpdate(BMCBase):
    pass


# BMC Item schemas
class BMCBlockType(str):
    key_partners = "key_partners"
    key_activities = "key_activities"
    key_resources = "key_resources"
    value_propositions = "value_propositions"
    customer_relationships = "customer_relationships"
    channels = "channels"
    customer_segments = "customer_segments"
    cost_structure = "cost_structure"
    revenue_streams = "revenue_streams"


class BMCItemBase(BaseModel):
    content: str = Field(..., max_length=1000)
    block: str = Field(..., description="The BMC block this item belongs to")
    position: Optional[int] = None


class BMCItemCreate(BMCItemBase):
    pass


class BMCItem(BMCItemBase):
    id: str
    project_id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BMCItemUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=1000)
    block: Optional[str] = None
    position: Optional[int] = None 