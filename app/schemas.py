from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChannelEnum(str, Enum):
    SLACK = "Slack"
    TELEGRAM = "Telegram"
    EMAIL = "Email"


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


class RowSchema(BaseModel):
    id: str  # noqa: VNE003
    channel: Optional[ChannelEnum] = Field(default=None, description="channel")
    timestamp: datetime
    raw_text: str


class LLMResponseSchema(BaseModel):
    category: str = CategoryEnum.OUT_OF_SCOPE
    priority: str = PriorityEnum.LOW
    target_department: Optional[str] = DepartmentEnum.OTHER
    short_summary: str
    needs_clarification: bool = True
    clarification_reason: Optional[str] = "None"


class ResultSchema(BaseModel):
    id: str  # noqa: VNE003
    channel: Optional[ChannelEnum] = Field(default=None, description="channel")
    short_summary: str
    category: str = CategoryEnum.OUT_OF_SCOPE
    target_department: Optional[str] = DepartmentEnum.OTHER
    priority: str = PriorityEnum.LOW
    needs_clarification: bool = True
    clarification_reason: Optional[str] = "None"

    @classmethod
    def get_fields_name(cls) -> list[str]:
        return list(cls.model_fields.keys())

    def get_fields_value(self) -> list[str]:
        values = []
        for _, value in self:
            if value is None:
                values.append("-")
            elif isinstance(value, Enum):
                values.append(value.value)
            else:
                values.append(str(value))
        return values


class LLMClassificationResponse(BaseModel):
    category: CategoryEnum = Field(
        default=CategoryEnum.OUT_OF_SCOPE,
        description="category"
    )
    target_department: Optional[DepartmentEnum] = Field(
        default=DepartmentEnum.OTHER,
        description="department or null"
    )
    priority: PriorityEnum = Field(
        default=PriorityEnum.LOW,
        description="priority"
    )
    short_summary: str = Field(description="short summary")
    needs_clarification: bool = Field(
        default=False,
        description="needs clarification"
    )
    clarification_reason: Optional[str] = Field(
        default="None",
        description="clarification reason"
    )
