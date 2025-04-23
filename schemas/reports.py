from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ReportFramework(str, Enum):
    CSD = "csd"
    PVB = "pvb"
    BMC = "bmc"
    RICE = "rice"
    ROADMAP = "roadmap"
    OKR = "okr"


class ReportRequest(BaseModel):
    frameworks: List[ReportFramework] = Field(..., min_items=1)
    include_cover_page: bool = True
    include_toc: bool = True 