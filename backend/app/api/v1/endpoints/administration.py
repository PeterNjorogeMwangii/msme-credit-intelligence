from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from backend.app.api.dependencies.auth import require_roles
from backend.app.database.session import get_db
from backend.app.schemas.administration import (
    AdministrationSummary,
    AuditListResponse,
    UserItem,
    UserListResponse,
    UserUpdateRequest,
)
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.services.administration_service import AdministrationService


ADMIN_ROLES = ("RISK_MANAGER", "SYSTEM_ADMIN")
router = APIRouter(
    prefix="/administration",
    tags=["Administration"],
    dependencies=[Depends(require_roles(*ADMIN_ROLES))],
)


@router.get("/summary", response_model=AdministrationSummary)
def summary(database: Session = Depends(get_db)):
    return AdministrationService(database).summary()


@router.get("/users", response_model=UserListResponse)
def users(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Optional[str] = None,
    role_code: Optional[str] = None,
    account_status: Optional[str] = None,
    database: Session = Depends(get_db),
):
    return AdministrationService(database).users(
        page=page,
        page_size=page_size,
        search=search,
        role=role_code,
        status=account_status,
    )


@router.patch("/users/{user_id}", response_model=UserItem)
def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(require_roles(*ADMIN_ROLES))],
    database: Session = Depends(get_db),
    x_change_reason: Annotated[Optional[str], Header()] = None,
):
    return AdministrationService(database).update_user(
        user_id,
        payload.role_code,
        payload.account_status,
        current_user.user_id,
        x_change_reason,
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
    )


@router.get("/audit-logs", response_model=AuditListResponse)
def audit_logs(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
    database: Session = Depends(get_db),
):
    return AdministrationService(database).audits(
        page=page,
        page_size=page_size,
        search=search,
        action=action,
        entity_type=entity_type,
        user_id=user_id,
    )
