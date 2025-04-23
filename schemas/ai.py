from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from schemas.csd import CSDCategory
from schemas.personas import PersonaDetailCategory


class AIPromptType(str, Enum):
    CSD = "csd"
    PVB = "pvb"
    BMC = "bmc"
    RICE = "rice"
    ROADMAP = "roadmap"
    OKR = "okr"
    PERSONA = "persona"


class AIPrompt(BaseModel):
    prompt_type: AIPromptType
    project_id: str
    context: Optional[str] = None
    specific_query: Optional[str] = None
    
    # For CSD specifically
    category: Optional[CSDCategory] = None
    
    # For PERSONA
    persona_category: Optional[PersonaDetailCategory] = None


class AISuggestion(BaseModel):
    suggestions: List[str]
    reasoning: Optional[str] = None 