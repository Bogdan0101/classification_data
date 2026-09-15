from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    ANALYTICS = "report/analytics"
    BUG_SUPPORT = "bug/support"
    CONSULTATION = "consultation/questions"
    OUT_OF_SCOPE = "out_of_scope"


class DepartmentEnum(str, Enum):
    MARKETING = "marketing"
    SALES = "sales"
    ANALYTICS = "analytics"
    PM = "project_manager"
    HR = "human_resources"
    OTHER = "other"


class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LLMClassificationResponse(BaseModel):
    category: CategoryEnum = Field(description="category")
    target_department: Optional[DepartmentEnum] = Field(
        default=None, description="department or null"
    )
    priority: PriorityEnum = Field(
        default=PriorityEnum.LOW,
        description="priority"
    )
    short_summary: str = Field(description="short summary")
    requested_actions: list[str] = Field(
        default_factory=list,
        description="list of specific actions",
    )
    needs_clarification: bool = Field(
        default=False,
        description="needs clarification"
    )
    clarification_reason: Optional[str] = Field(
        default=None,
        description="clarification reason"
    )
