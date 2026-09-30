import json
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class AuthRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def find_by_username(self, username: str) -> Optional[dict[str, Any]]:
        row = self.database.execute(
            text(
                """
                SELECT user_id, username, email, full_name, password_hash,
                       role_code, employee_number, branch_code, account_status,
                       failed_login_attempts, last_login_at
                  FROM security.users
                 WHERE lower(username) = lower(:username)
                 LIMIT 1
                """
            ),
            {"username": username.strip()},
        ).mappings().first()
        return dict(row) if row else None

    def find_by_id(self, user_id: UUID) -> Optional[dict[str, Any]]:
        row = self.database.execute(
            text(
                """
                SELECT user_id, username, email, full_name, role_code,
                       employee_number, branch_code, account_status, last_login_at
                  FROM security.users
                 WHERE user_id = :user_id
                 LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).mappings().first()
        return dict(row) if row else None

    def record_failed_login(self, user_id: UUID, attempts: int, locked: bool) -> None:
        self.database.execute(
            text(
                """
                UPDATE security.users
                   SET failed_login_attempts = :attempts,
                       account_status = CASE WHEN :locked THEN 'LOCKED' ELSE account_status END,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE user_id = :user_id
                """
            ),
            {"attempts": attempts, "locked": locked, "user_id": user_id},
        )

    def record_successful_login(self, user_id: UUID) -> dict[str, Any]:
        row = self.database.execute(
            text(
                """
                UPDATE security.users
                   SET failed_login_attempts = 0,
                       last_login_at = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP
                 WHERE user_id = :user_id
             RETURNING user_id, username, email, full_name, role_code,
                       employee_number, branch_code, account_status, last_login_at
                """
            ),
            {"user_id": user_id},
        ).mappings().one()
        return dict(row)

    def add_audit(
        self,
        *,
        user_id: Optional[UUID],
        action: str,
        entity_id: str,
        reason: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        new_value: Optional[dict[str, Any]] = None,
    ) -> None:
        self.database.execute(
            text(
                """
                INSERT INTO security.audit_logs (
                    audit_id, user_id, action, entity_type, entity_id,
                    previous_value, new_value, reason, ip_address,
                    user_agent, correlation_id, action_timestamp
                ) VALUES (
                    :audit_id, :user_id, :action, 'AUTHENTICATION', :entity_id,
                    NULL, CAST(:new_value AS jsonb), :reason, CAST(:ip_address AS inet),
                    :user_agent, :correlation_id, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "audit_id": uuid4(),
                "user_id": user_id,
                "action": action,
                "entity_id": entity_id,
                "new_value": json.dumps(new_value) if new_value else None,
                "reason": reason,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "correlation_id": uuid4(),
            },
        )
