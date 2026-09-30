from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

RoleCode = Literal["CREDIT_ANALYST", "CREDIT_MANAGER", "RISK_MANAGER", "SYSTEM_ADMIN"]
AccountStatus = Literal["ACTIVE", "LOCKED", "DISABLED"]


class UserItem(BaseModel):
    user_id: UUID
    username: str
    email: str
    full_name: str
    role_code: str
    employee_number: Optional[str] = None
    branch_code: Optional[str] = None
    account_status: str
    failed_login_attempts: int
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: list[UserItem]


class UserUpdateRequest(BaseModel):
    role_code: Optional[RoleCode] = None
    account_status: Optional[AccountStatus] = None

    @model_validator(mode="after")
    def require_change(self):
        if self.role_code is None and self.account_status is None:
            raise ValueError("Provide role_code or account_status")
        return self


class AuditItem(BaseModel):
    audit_id: UUID
    user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    previous_value: Optional[dict[str, Any]] = None
    new_value: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: UUID
    action_timestamp: datetime


class AuditListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: list[AuditItem]


class AdministrationSummary(BaseModel):
    total_users: int
    active_users: int
    locked_users: int
    disabled_users: int
    failed_login_attempts: int
    audit_events_24h: int
