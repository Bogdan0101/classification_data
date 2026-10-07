from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChannelEnum(str, Enum):
    SLACK = "Slack"
    TELEGRAM = "Telegram"
    EMAIL = "Email"


class RowSchema(BaseModel):
    id: str   # noqa: VNE003
    channel: Optional[ChannelEnum] = Field(default=None, description="channel")
    timestamp: datetime
    raw_text: str


class LLMResponseSchema(BaseModel):
    category: str = "out_of_scope"
    priority: str = "low"
    target_department: Optional[str] = "unassigned"
    short_summary: str = "None"
    needs_clarification: bool = True
    clarification_reason: Optional[str] = "None"


class ResultSchema(RowSchema, LLMResponseSchema):
    pass


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
