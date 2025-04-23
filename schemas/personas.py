from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PersonaDetailCategory(str, Enum):
    GOAL = "Goal"
    NEED = "Need"
    PAIN_POINT = "Pain Point" 
    MOTIVATION = "Motivation"


class PersonaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    photo_url: Optional[str] = None
    quote: Optional[str] = None
    demographics: Optional[str] = None
    bio: Optional[str] = None


class PersonaCreate(PersonaBase):
    project_id: str


class Persona(PersonaBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PersonaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    photo_url: Optional[str] = None
    quote: Optional[str] = None
    demographics: Optional[str] = None
    bio: Optional[str] = None


class PersonaList(BaseModel):
    personas: List[Persona]


class PersonaDetailBase(BaseModel):
    category: PersonaDetailCategory
    content: str = Field(..., min_length=1, max_length=500)
    order_index: int = 0


class PersonaDetailCreate(PersonaDetailBase):
    persona_id: str


class PersonaDetail(PersonaDetailBase):
    id: str
    persona_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PersonaDetailUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[PersonaDetailCategory] = None
    order_index: Optional[int] = None


class PersonaDetailList(BaseModel):
    details: List[PersonaDetail]
    
class PersonaDetailReorder(BaseModel):
    """
    Schema for reordering Persona details through drag and drop
    """
    item_ids: List[str] = Field(..., description="Ordered list of Persona detail IDs after reordering")
    new_category: Optional[PersonaDetailCategory] = Field(None, description="New category if items are dragged to a different section") 