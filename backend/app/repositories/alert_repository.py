from typing import Any, Optional, Dict, Tuple
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _filters(
        status: Optional[str],
        severity: Optional[str],
        alert_type: Optional[str],
        customer_id: Optional[str],
        assigned_to: Optional[UUID],
        unassigned: bool,
        search: Optional[str],
    ) -> Tuple[str, Dict[str, Any]]:
        clauses: list[str] = []
        params: Dict[str, Any] = {}
        if status:
            clauses.append("a.alert_status = :status")
            params["status"] = status
        if severity:
            clauses.append("a.severity = :severity")
            params["severity"] = severity
        if alert_type:
            clauses.append("a.alert_type = :alert_type")
            params["alert_type"] = alert_type
        if customer_id:
            clauses.append("a.customer_id = :customer_id")
            params["customer_id"] = customer_id
        if assigned_to:
            clauses.append("a.assigned_to = :assigned_to")
            params["assigned_to"] = assigned_to
        if unassigned:
            clauses.append("a.assigned_to IS NULL")
        if search:
            clauses.append("""(
                a.customer_id ILIKE :search OR
                c.legal_name ILIKE :search OR
                c.trading_name ILIKE :search OR
                a.alert_title ILIKE :search OR
                COALESCE(a.loan_id, '') ILIKE :search
            )""")
            params["search"] = f"%{search}%"
        return (" WHERE " + " AND ".join(clauses)) if clauses else "", params

    def list_alerts(
        self,
        offset: int,
        limit: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        customer_id: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        unassigned: bool = False,
        search: Optional[str] = None,
    ) -> Tuple[int, list[Dict[str, Any]]]:
        where, params = self._filters(
            status, severity, alert_type, customer_id, assigned_to, unassigned, search
        )
        joins = """
            FROM credit.risk_alerts a
            JOIN banking.customers c ON c.customer_id = a.customer_id
            LEFT JOIN security.users u ON u.user_id = a.assigned_to
        """
        total = self.db.execute(
            text("SELECT COUNT(*) " + joins + where), params
        ).scalar_one()
        rows = self.db.execute(
            text(
                """
                SELECT a.alert_id, a.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS customer_name,
                       a.loan_id, a.alert_type, a.severity, a.alert_title,
                       a.alert_description, a.trigger_value, a.threshold_value,
                       a.alert_status, a.assigned_to,
                       COALESCE(u.full_name, u.username) AS assignee_name,
                       a.detected_at, a.acknowledged_at, a.resolved_at
                """
                + joins
                + where
                + " ORDER BY CASE a.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 "
                  "WHEN 'MEDIUM' THEN 3 ELSE 4 END, a.detected_at DESC "
                  "LIMIT :limit OFFSET :offset"
            ),
            {**params, "limit": limit, "offset": offset},
        ).mappings().all()
        return int(total), [dict(row) for row in rows]

    def get_summary(self) -> Dict[str, Any]:
        row = self.db.execute(
            text("""
                SELECT COUNT(*) AS total_alerts,
                    COUNT(*) FILTER (WHERE alert_status = 'OPEN') AS open_alerts,
                    COUNT(*) FILTER (WHERE alert_status = 'ACKNOWLEDGED') AS acknowledged_alerts,
                    COUNT(*) FILTER (WHERE alert_status = 'UNDER_INVESTIGATION') AS under_investigation_alerts,
                    COUNT(*) FILTER (WHERE alert_status = 'RESOLVED') AS resolved_alerts,
                    COUNT(*) FILTER (WHERE alert_status = 'DISMISSED') AS dismissed_alerts,
                    COUNT(*) FILTER (WHERE severity = 'CRITICAL' AND alert_status IN ('OPEN','ACKNOWLEDGED','UNDER_INVESTIGATION')) AS critical_open_alerts,
                    COUNT(*) FILTER (WHERE severity = 'HIGH' AND alert_status IN ('OPEN','ACKNOWLEDGED','UNDER_INVESTIGATION')) AS high_open_alerts,
                    COUNT(*) FILTER (WHERE assigned_to IS NULL AND alert_status IN ('OPEN','ACKNOWLEDGED','UNDER_INVESTIGATION')) AS unassigned_open_alerts,
                    COUNT(DISTINCT customer_id) FILTER (WHERE alert_status IN ('OPEN','ACKNOWLEDGED','UNDER_INVESTIGATION')) AS affected_customers
                FROM credit.risk_alerts
            """)
        ).mappings().one()
        return dict(row)

    def get_alert(self, alert_id: UUID) -> Optional[Dict[str, Any]]:
        row = self.db.execute(
            text("""
                SELECT a.alert_id, a.customer_id,
                       COALESCE(c.trading_name, c.legal_name) AS customer_name,
                       a.loan_id, a.alert_type, a.severity, a.alert_title,
                       a.alert_description, a.trigger_value, a.threshold_value,
                       a.alert_status, a.assigned_to,
                       COALESCE(u.full_name, u.username) AS assignee_name,
                       a.detected_at, a.acknowledged_at, a.resolved_at,
                       a.resolution_notes, a.created_at
                FROM credit.risk_alerts a
                JOIN banking.customers c ON c.customer_id = a.customer_id
                LEFT JOIN security.users u ON u.user_id = a.assigned_to
                WHERE a.alert_id = :alert_id
            """),
            {"alert_id": alert_id},
        ).mappings().first()
        return dict(row) if row else None

    def acknowledge(self, alert_id: UUID, assigned_to: Optional[UUID]) -> bool:
        result = self.db.execute(
            text("""
                UPDATE credit.risk_alerts
                SET alert_status = 'ACKNOWLEDGED',
                    acknowledged_at = COALESCE(acknowledged_at, CURRENT_TIMESTAMP),
                    assigned_to = COALESCE(:assigned_to, assigned_to)
                WHERE alert_id = :alert_id AND alert_status = 'OPEN'
            """),
            {"alert_id": alert_id, "assigned_to": assigned_to},
        )
        return result.rowcount == 1

    def assign(self, alert_id: UUID, assigned_to: UUID, investigate: bool) -> bool:
        result = self.db.execute(
            text("""
                UPDATE credit.risk_alerts
                SET assigned_to = :assigned_to,
                    alert_status = CASE
                        WHEN :investigate AND alert_status IN ('OPEN','ACKNOWLEDGED')
                        THEN 'UNDER_INVESTIGATION' ELSE alert_status END,
                    acknowledged_at = CASE
                        WHEN acknowledged_at IS NULL THEN CURRENT_TIMESTAMP
                        ELSE acknowledged_at END
                WHERE alert_id = :alert_id
                  AND alert_status NOT IN ('RESOLVED','DISMISSED')
            """),
            {"alert_id": alert_id, "assigned_to": assigned_to, "investigate": investigate},
        )
        return result.rowcount == 1

    def resolve(self, alert_id: UUID, resolution: str, notes: str) -> bool:
        result = self.db.execute(
            text("""
                UPDATE credit.risk_alerts
                SET alert_status = :resolution,
                    resolved_at = CURRENT_TIMESTAMP,
                    resolution_notes = :notes,
                    acknowledged_at = COALESCE(acknowledged_at, CURRENT_TIMESTAMP)
                WHERE alert_id = :alert_id
                  AND alert_status NOT IN ('RESOLVED','DISMISSED')
            """),
            {"alert_id": alert_id, "resolution": resolution, "notes": notes},
        )
        return result.rowcount == 1

