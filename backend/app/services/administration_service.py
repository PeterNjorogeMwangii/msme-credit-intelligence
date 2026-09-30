from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.repositories.administration_repository import AdministrationRepository


class AdministrationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AdministrationRepository(db)

    def summary(self):
        return self.repo.summary()

    def users(self, **kwargs):
        return self.repo.list_users(**kwargs)

    def audits(self, **kwargs):
        return self.repo.list_audits(**kwargs)

    def update_user(
        self,
        user_id: UUID,
        role_code: Optional[str],
        account_status: Optional[str],
        actor_id: Optional[UUID],
        reason: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ):
        result = self.repo.update_user(
            user_id, role_code, account_status, actor_id, reason, ip_address, user_agent
        )
        if not result:
            self.db.rollback()
            raise HTTPException(status_code=404, detail="User was not found.")
        self.db.commit()
        return result
