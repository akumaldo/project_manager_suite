from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime


class RICEItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    reach_score: int = Field(..., ge=0, le=10)
    impact_score: int = Field(..., ge=0, le=10)
    confidence_score: int = Field(..., ge=0, le=10)
    effort_score: int = Field(..., ge=1, le=10)
    
    @computed_field
    def rice_score(self) -> float:
        """
        Calculate RICE score: (Reach × Impact × Confidence) ÷ Effort
        """
        if self.effort_score == 0:
            return 0
        return (self.reach_score * self.impact_score * self.confidence_score) / self.effort_score


class RICEItemCreate(RICEItemBase):
    project_id: str


class RICEItem(RICEItemBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RICEItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    reach_score: Optional[int] = Field(None, ge=0, le=10)
    impact_score: Optional[int] = Field(None, ge=0, le=10)
    confidence_score: Optional[int] = Field(None, ge=0, le=10)
    effort_score: Optional[int] = Field(None, ge=1, le=10)


class RICEItemList(BaseModel):
    items: List[RICEItem] 