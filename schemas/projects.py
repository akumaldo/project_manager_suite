from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class ProjectList(BaseModel):
    projects: List[Project] 