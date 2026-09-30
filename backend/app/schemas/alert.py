from datetime import datetime

from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


AlertStatus = Literal[
    "OPEN", "ACKNOWLEDGED", "UNDER_INVESTIGATION", "RESOLVED", "DISMISSED"
]
AlertSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class AlertListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: UUID
    customer_id: str
    customer_name: Optional[str] = None
    loan_id: Optional[str] = None
    alert_type: str
    severity: AlertSeverity
    alert_title: str
    alert_description: str
    trigger_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    alert_status: AlertStatus
    assigned_to: Optional[UUID] = None
    assignee_name: Optional[str] = None
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertDetail(AlertListItem):
    resolution_notes: Optional[str] = None
    created_at: datetime


class AlertListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: list[AlertListItem]


class AlertSummaryResponse(BaseModel):
    total_alerts: int
    open_alerts: int
    acknowledged_alerts: int
    under_investigation_alerts: int
    resolved_alerts: int
    dismissed_alerts: int
    critical_open_alerts: int
    high_open_alerts: int
    unassigned_open_alerts: int
    affected_customers: int


class AlertAcknowledgeRequest(BaseModel):
    assigned_to: Optional[UUID] = None


class AlertAssignRequest(BaseModel):
    assigned_to: UUID
    move_to_investigation: bool = True


class AlertResolveRequest(BaseModel):
    resolution_notes: str = Field(min_length=3, max_length=4000)
    resolution: Literal["RESOLVED", "DISMISSED"] = "RESOLVED"

