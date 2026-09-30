import json
import math
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


class AdministrationRepository:
    def __init__(self, db: Session):
        self.db = db

    def summary(self) -> dict[str, Any]:
        return dict(
            self.db.execute(
                text("""
                    SELECT COUNT(*)::integer total_users,
                      COUNT(*) FILTER (WHERE account_status='ACTIVE')::integer active_users,
                      COUNT(*) FILTER (WHERE account_status='LOCKED')::integer locked_users,
                      COUNT(*) FILTER (WHERE account_status='DISABLED')::integer disabled_users,
                      COALESCE(SUM(failed_login_attempts),0)::integer failed_login_attempts,
                      (SELECT COUNT(*)::integer FROM security.audit_logs
                       WHERE action_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours') audit_events_24h
                    FROM security.users
                """)
            )
            .mappings()
            .one()
        )

    def list_users(
        self,
        page: int,
        page_size: int,
        search: Optional[str],
        role: Optional[str],
        status: Optional[str],
    ) -> dict[str, Any]:
        conditions = ["1=1"]
        params: dict[str, Any] = {}

        if search:
            conditions.append(
                "(username ILIKE :search OR email ILIKE :search OR full_name ILIKE :search OR COALESCE(employee_number,'') ILIKE :search)"
            )
            params["search"] = f"%{search.strip()}%"

        if role:
            conditions.append("role_code=:role")
            params["role"] = role

        if status:
            conditions.append("account_status=:status")
            params["status"] = status

        where = " AND ".join(conditions)
        total = self.db.execute(
            text("SELECT COUNT(*) FROM security.users WHERE " + where), params
        ).scalar_one()

        rows = self.db.execute(
            text(
                """SELECT user_id,username,email,full_name,role_code,employee_number,
                branch_code,account_status,failed_login_attempts,last_login_at,created_at,updated_at
                FROM security.users WHERE """
                + where
                + " ORDER BY full_name LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()

        return {
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": math.ceil(total / page_size) if total else 0,
            "records": [dict(r) for r in rows],
        }

    def get_user(self, user_id: UUID) -> Optional[dict[str, Any]]:
        row = self.db.execute(
            text(
                """SELECT user_id,username,email,full_name,role_code,employee_number,
                branch_code,account_status,failed_login_attempts,last_login_at,created_at,updated_at
                FROM security.users WHERE user_id=:id"""
            ),
            {"id": user_id},
        ).mappings().first()
        return dict(row) if row else None

    def update_user(
        self,
        user_id: UUID,
        role_code: Optional[str],
        account_status: Optional[str],
        actor_id: Optional[UUID],
        reason: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> Optional[dict[str, Any]]:
        previous = self.get_user(user_id)
        if not previous:
            return None

        self.db.execute(
            text(
                """UPDATE security.users SET role_code=COALESCE(:role,role_code),
                account_status=COALESCE(:status,account_status),updated_at=CURRENT_TIMESTAMP WHERE user_id=:id"""
            ),
            {"role": role_code, "status": account_status, "id": user_id},
        )

        changed = {
            "role_code": role_code or previous["role_code"],
            "account_status": account_status or previous["account_status"],
        }

        self.db.execute(
            text(
                """INSERT INTO security.audit_logs(audit_id,user_id,action,entity_type,entity_id,
                previous_value,new_value,reason,ip_address,user_agent,correlation_id,action_timestamp)
                VALUES(:audit_id,:actor,'UPDATE_USER','SECURITY_USER',:entity_id,CAST(:previous AS jsonb),
                CAST(:new AS jsonb),:reason,CAST(:ip AS inet),:agent,:correlation,CURRENT_TIMESTAMP)"""
            ),
            {
                "audit_id": uuid4(),
                "actor": actor_id,
                "entity_id": str(user_id),
                "previous": json.dumps(
                    {"role_code": previous["role_code"], "account_status": previous["account_status"]}
                ),
                "new": json.dumps(changed),
                "reason": reason,
                "ip": ip_address,
                "agent": user_agent,
                "correlation": uuid4(),
            },
        )
        return self.get_user(user_id)

    def list_audits(
        self,
        page: int,
        page_size: int,
        search: Optional[str],
        action: Optional[str],
        entity_type: Optional[str],
        user_id: Optional[UUID],
    ) -> dict[str, Any]:
        conditions = ["1=1"]
        params: dict[str, Any] = {}

        if search:
            conditions.append(
                "(a.action ILIKE :search OR a.entity_type ILIKE :search OR a.entity_id ILIKE :search OR COALESCE(a.reason,'') ILIKE :search OR COALESCE(u.full_name,'') ILIKE :search)"
            )
            params["search"] = f"%{search.strip()}%"

        if action:
            conditions.append("a.action=:action")
            params["action"] = action

        if entity_type:
            conditions.append("a.entity_type=:entity_type")
            params["entity_type"] = entity_type

        if user_id:
            conditions.append("a.user_id=:user_id")
            params["user_id"] = user_id

        where = " AND ".join(conditions)
        joins = " FROM security.audit_logs a LEFT JOIN security.users u ON u.user_id=a.user_id "

        total = self.db.execute(
            text("SELECT COUNT(*) " + joins + " WHERE " + where), params
        ).scalar_one()

        rows = self.db.execute(
            text(
                """SELECT a.audit_id,a.user_id,u.full_name actor_name,a.action,a.entity_type,
                a.entity_id,a.previous_value,a.new_value,a.reason,a.ip_address::text ip_address,
                a.user_agent,a.correlation_id,a.action_timestamp"""
                + joins
                + " WHERE "
                + where
                + " ORDER BY a.action_timestamp DESC LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        ).mappings().all()

        return {
            "page": page,
            "page_size": page_size,
            "total_records": total,
            "total_pages": math.ceil(total / page_size) if total else 0,
            "records": [dict(r) for r in rows],
        }
