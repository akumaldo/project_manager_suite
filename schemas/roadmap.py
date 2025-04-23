from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class RoadmapStatus(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DELAYED = "Delayed"


class RoadmapQuarter(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class RoadmapPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RoadmapTimeframe(str, Enum):
    NOW = "now"
    NEXT = "next"
    LATER = "later"


class RoadmapItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quarter: RoadmapQuarter
    year: int = Field(..., ge=2000, le=2100)
    status: RoadmapStatus = RoadmapStatus.PLANNED
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: Optional[RoadmapPriority] = RoadmapPriority.MEDIUM
    timeframe: Optional[RoadmapTimeframe] = RoadmapTimeframe.NEXT
    position: Optional[int] = None
    # content field for frontend compatibility
    content: Optional[str] = Field(None, max_length=500)


class RoadmapItemCreate(RoadmapItemBase):
    project_id: str


class RoadmapItem(RoadmapItemBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoadmapItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quarter: Optional[RoadmapQuarter] = None
    year: Optional[int] = Field(None, ge=2000, le=2100)
    status: Optional[RoadmapStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: Optional[RoadmapPriority] = None
    timeframe: Optional[RoadmapTimeframe] = None
    position: Optional[int] = None
    content: Optional[str] = Field(None, max_length=500)


class RoadmapItemList(BaseModel):
    items: List[RoadmapItem] 