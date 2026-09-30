import math
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.repositories.alert_repository import AlertRepository
from backend.app.schemas.alert import (
    AlertDetail,
    AlertListResponse,
    AlertSummaryResponse,
)


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AlertRepository(db)

    def list_alerts(self, page: int, page_size: int, **filters) -> AlertListResponse:
        total, records = self.repository.list_alerts(
            offset=(page - 1) * page_size, limit=page_size, **filters
        )
        return AlertListResponse(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=math.ceil(total / page_size) if total else 0,
            records=records,
        )

    def summary(self) -> AlertSummaryResponse:
        return AlertSummaryResponse(**self.repository.get_summary())

    def detail(self, alert_id: UUID) -> AlertDetail:
        alert = self.repository.get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert was not found.")
        return AlertDetail(**alert)

    def _commit_and_return(self, alert_id: UUID) -> AlertDetail:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The assigned user does not exist or the update violates a database rule.",
            ) from exc
        return self.detail(alert_id)

    def acknowledge(self, alert_id: UUID, assigned_to: Optional[UUID]) -> AlertDetail:
        if not self.repository.acknowledge(alert_id, assigned_to):
            self._raise_invalid_state(alert_id, "Only an OPEN alert can be acknowledged.")
        return self._commit_and_return(alert_id)

    def assign(self, alert_id: UUID, assigned_to: UUID, investigate: bool) -> AlertDetail:
        if not self.repository.assign(alert_id, assigned_to, investigate):
            self._raise_invalid_state(alert_id, "A closed alert cannot be assigned.")
        return self._commit_and_return(alert_id)

    def resolve(self, alert_id: UUID, resolution: str, notes: str) -> AlertDetail:
        if not self.repository.resolve(alert_id, resolution, notes):
            self._raise_invalid_state(alert_id, "The alert is already closed.")
        return self._commit_and_return(alert_id)

    def _raise_invalid_state(self, alert_id: UUID, message: str) -> None:
        if not self.repository.get_alert(alert_id):
            raise HTTPException(status_code=404, detail="Alert was not found.")
        raise HTTPException(status_code=409, detail=message)

