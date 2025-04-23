from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class OKRStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    AT_RISK = "At Risk"


class ObjectiveBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    status: OKRStatus = OKRStatus.NOT_STARTED


class ObjectiveCreate(ObjectiveBase):
    project_id: str


class Objective(ObjectiveBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ObjectiveUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[OKRStatus] = None


class KeyResultBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    current_value: float = 0.0
    target_value: float = Field(..., gt=0.0)
    status: OKRStatus = OKRStatus.NOT_STARTED


class KeyResultCreate(KeyResultBase):
    objective_id: str


class KeyResult(KeyResultBase):
    id: str
    objective_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
    
    @property
    def progress(self) -> float:
        """Calculate progress as percentage of target achieved"""
        if self.target_value == 0:
            return 0
        return min(100.0, (self.current_value / self.target_value) * 100)


class KeyResultUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    current_value: Optional[float] = None
    target_value: Optional[float] = Field(None, gt=0.0)
    status: Optional[OKRStatus] = None


class ObjectiveWithKeyResults(Objective):
    key_results: List[KeyResult] = []


class ObjectiveList(BaseModel):
    objectives: List[ObjectiveWithKeyResults] 