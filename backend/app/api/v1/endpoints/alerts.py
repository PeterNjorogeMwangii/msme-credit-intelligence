from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.alert import (
    AlertAcknowledgeRequest,
    AlertAssignRequest,
    AlertDetail,
    AlertListResponse,
    AlertResolveRequest,
    AlertSummaryResponse,
)
from backend.app.services.alert_service import AlertService


router = APIRouter(prefix="/alerts", tags=["Risk Alerts"])


@router.get("/summary", response_model=AlertSummaryResponse)
def get_alert_summary(database: Session = Depends(get_db)) -> AlertSummaryResponse:
    return AlertService(database).summary()


@router.get("", response_model=AlertListResponse)
def list_alerts(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    alert_status: Annotated[Optional[str], Query(pattern="^(OPEN|ACKNOWLEDGED|UNDER_INVESTIGATION|RESOLVED|DISMISSED)$")] = None,
    severity: Annotated[Optional[str], Query(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")] = None,
    alert_type: Optional[str] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    unassigned: bool = False,
    search: Optional[str] = None,
    database: Session = Depends(get_db),
) -> AlertListResponse:
    return AlertService(database).list_alerts(
        page=page,
        page_size=page_size,
        status=alert_status,
        severity=severity,
        alert_type=alert_type,
        customer_id=customer_id,
        assigned_to=assigned_to,
        unassigned=unassigned,
        search=search,
    )


@router.get("/{alert_id}", response_model=AlertDetail)
def get_alert(alert_id: UUID, database: Session = Depends(get_db)) -> AlertDetail:
    return AlertService(database).detail(alert_id)


@router.patch("/{alert_id}/acknowledge", response_model=AlertDetail)
def acknowledge_alert(
    alert_id: UUID,
    payload: AlertAcknowledgeRequest,
    database: Session = Depends(get_db),
) -> AlertDetail:
    return AlertService(database).acknowledge(alert_id, payload.assigned_to)


@router.patch("/{alert_id}/assign", response_model=AlertDetail)
def assign_alert(
    alert_id: UUID,
    payload: AlertAssignRequest,
    database: Session = Depends(get_db),
) -> AlertDetail:
    return AlertService(database).assign(
        alert_id, payload.assigned_to, payload.move_to_investigation
    )


@router.patch("/{alert_id}/resolve", response_model=AlertDetail)
def resolve_alert(
    alert_id: UUID,
    payload: AlertResolveRequest,
    database: Session = Depends(get_db),
) -> AlertDetail:
    return AlertService(database).resolve(
        alert_id, payload.resolution, payload.resolution_notes
    )

