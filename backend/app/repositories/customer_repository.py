from typing import Any, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_customers(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_band: Optional[str] = None,
    ) -> int:
        conditions = ["1 = 1"]
        parameters: dict[str, Any] = {}
        if search:
            conditions.append(
                "(c.customer_id ILIKE :search OR c.customer_number ILIKE :search "
                "OR c.legal_name ILIKE :search OR c.trading_name ILIKE :search)"
            )
            parameters["search"] = f"%{search.strip()}%"
        if status:
            conditions.append("c.record_status = :status")
            parameters["status"] = status
        if risk_band:
            conditions.append("""
                EXISTS (
                    SELECT 1
                    FROM credit.loan_applications app
                    JOIN credit.credit_assessments ca
                      ON ca.application_id = app.application_id
                    WHERE app.customer_id = c.customer_id
                      AND ca.risk_band = :risk_band
                )
            """)
            parameters["risk_band"] = risk_band
        return int(
            self.db.execute(
                text(
                    "SELECT COUNT(*) FROM banking.customers c WHERE "
                    + " AND ".join(conditions)
                ),
                parameters,
            ).scalar_one()
        )

    def list_customers(
        self,
        offset: int,
        limit: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        risk_band: Optional[str] = None,
    ) -> List[Customer]:
        conditions = ["1 = 1"]
        parameters: dict[str, Any] = {"offset": offset, "limit": limit}
        if search:
            conditions.append(
                "(c.customer_id ILIKE :search OR c.customer_number ILIKE :search "
                "OR c.legal_name ILIKE :search OR c.trading_name ILIKE :search)"
            )
            parameters["search"] = f"%{search.strip()}%"
        if status:
            conditions.append("c.record_status = :status")
            parameters["status"] = status
        if risk_band:
            conditions.append("""
                EXISTS (
                    SELECT 1
                    FROM credit.loan_applications app
                    JOIN credit.credit_assessments ca
                      ON ca.application_id = app.application_id
                    WHERE app.customer_id = c.customer_id
                      AND ca.risk_band = :risk_band
                )
            """)
            parameters["risk_band"] = risk_band
        rows = self.db.execute(
            text(
                """
                SELECT c.customer_id, c.legal_name, c.trading_name,
                       c.record_status, c.aml_risk_classification,
                       c.created_at, c.updated_at
                FROM banking.customers c
                WHERE
                """
                + " AND ".join(conditions)
                + " ORDER BY COALESCE(c.trading_name, c.legal_name), c.customer_id "
                  "LIMIT :limit OFFSET :offset"
            ),
            parameters,
        ).mappings().all()
        return list(rows)

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.customer_id == customer_id)
            .first()
        )

    def get_financial_summary(self, customer_id: str) -> dict[str, Any]:
        account_summary = self.db.execute(
            text(
                """
                WITH latest_balances AS (
                    SELECT DISTINCT ON (t.account_id)
                           t.account_id,
                           t.balance_after
                    FROM banking.account_transactions t
                    WHERE t.customer_id = :customer_id
                      AND COALESCE(t.reversal_flag, false) = false
                    ORDER BY t.account_id,
                             t.value_date DESC,
                             t.posting_timestamp DESC
                )
                SELECT COUNT(a.account_id)::integer AS account_count,
                       COUNT(a.account_id) FILTER (
                           WHERE a.account_status = 'ACTIVE'
                       )::integer AS active_account_count,
                       COALESCE(SUM(lb.balance_after), 0)::numeric
                           AS estimated_total_balance
                FROM banking.accounts a
                LEFT JOIN latest_balances lb ON lb.account_id = a.account_id
                WHERE a.customer_id = :customer_id
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        transaction_summary = self.db.execute(
            text(
                """
                WITH anchor AS (
                    SELECT COALESCE(MAX(value_date), CURRENT_DATE) AS max_date
                    FROM banking.account_transactions
                    WHERE customer_id = :customer_id
                )
                SELECT COUNT(*)::integer AS transaction_count_180d,
                       COALESCE(SUM(t.local_currency_amount) FILTER (
                           WHERE t.credit_debit_indicator = 'C'
                       ), 0)::numeric AS total_credits_180d,
                       COALESCE(SUM(t.local_currency_amount) FILTER (
                           WHERE t.credit_debit_indicator = 'D'
                       ), 0)::numeric AS total_debits_180d,
                       COALESCE(
                           SUM(CASE
                               WHEN t.credit_debit_indicator = 'C'
                                   THEN t.local_currency_amount
                               ELSE -t.local_currency_amount
                           END),
                           0
                       )::numeric AS net_cash_flow_180d,
                       COALESCE(AVG(t.local_currency_amount), 0)::numeric
                           AS average_transaction_amount_180d,
                       COUNT(*) FILTER (
                           WHERE COALESCE(t.cash_transaction_flag, false) = true
                       )::integer AS cash_transaction_count_180d
                FROM banking.account_transactions t
                CROSS JOIN anchor
                WHERE t.customer_id = :customer_id
                  AND t.value_date >= anchor.max_date - INTERVAL '180 days'
                  AND t.value_date <= anchor.max_date
                  AND COALESCE(t.reversal_flag, false) = false
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        application_summary = self.db.execute(
            text(
                """
                SELECT COUNT(*)::integer AS application_count,
                       COUNT(*) FILTER (
                           WHERE application_status IN ('APPROVED', 'DISBURSED')
                       )::integer AS approved_application_count,
                       COUNT(*) FILTER (
                           WHERE application_status = 'DECLINED'
                       )::integer AS declined_application_count,
                       COALESCE(SUM(requested_amount), 0)::numeric
                           AS total_requested_amount
                FROM credit.loan_applications
                WHERE customer_id = :customer_id
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        loan_summary = self.db.execute(
            text(
                """
                SELECT COUNT(l.loan_id)::integer AS loan_count,
                       COUNT(l.loan_id) FILTER (
                           WHERE l.loan_status IN (
                               'ACTIVE', 'IN_ARREARS', 'RESTRUCTURED'
                           )
                       )::integer AS active_loan_count,
                       COALESCE(SUM(l.original_principal), 0)::numeric
                           AS total_original_principal,
                       COALESCE(SUM(l.outstanding_principal), 0)::numeric
                           AS total_outstanding_principal,
                       COALESCE(SUM(l.arrears_amount), 0)::numeric
                           AS total_arrears,
                       COALESCE(MAX(l.days_past_due), 0)::integer
                           AS maximum_days_past_due
                FROM banking.loans l
                JOIN credit.loan_applications app
                  ON app.application_id = l.application_id
                WHERE app.customer_id = :customer_id
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        repayment_summary = self.db.execute(
            text(
                """
                SELECT COUNT(rs.schedule_id)::integer
                           AS scheduled_installment_count,
                       COUNT(rs.schedule_id) FILTER (
                           WHERE rs.schedule_status IN ('OVERDUE', 'PARTIALLY_PAID')
                       )::integer AS overdue_installment_count,
                       COALESCE(SUM(rs.total_amount_due), 0)::numeric
                           AS scheduled_amount_due,
                       COALESCE(SUM(rs.amount_paid), 0)::numeric
                           AS scheduled_amount_paid,
                       COALESCE(SUM(rs.outstanding_amount), 0)::numeric
                           AS scheduled_outstanding_amount
                FROM banking.repayment_schedule rs
                JOIN banking.loans l ON l.loan_id = rs.loan_id
                JOIN credit.loan_applications app
                  ON app.application_id = l.application_id
                WHERE app.customer_id = :customer_id
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        return {
            **dict(account_summary),
            **dict(transaction_summary),
            **dict(application_summary),
            **dict(loan_summary),
            **dict(repayment_summary),
        }

    def get_risk_summary(self, customer_id: str) -> dict[str, Any]:
        latest_assessment = self.db.execute(
            text(
                """
                SELECT to_jsonb(ca) AS record
                FROM credit.credit_assessments ca
                JOIN credit.loan_applications app
                  ON app.application_id = ca.application_id
                WHERE app.customer_id = :customer_id
                ORDER BY ca.assessment_timestamp DESC,
                         ca.assessment_version DESC
                LIMIT 1
                """
            ),
            {"customer_id": customer_id},
        ).scalar_one_or_none()

        latest_bureau = self.db.execute(
            text(
                """
                SELECT to_jsonb(br) AS record
                FROM banking.credit_bureau_reports br
                JOIN credit.loan_applications app
                  ON app.application_id = br.application_id
                WHERE app.customer_id = :customer_id
                ORDER BY br.report_date DESC, br.created_at DESC
                LIMIT 1
                """
            ),
            {"customer_id": customer_id},
        ).scalar_one_or_none()

        alert_summary = self.db.execute(
            text(
                """
                SELECT COUNT(*) FILTER (
                           WHERE alert_status IN (
                               'OPEN', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION'
                           )
                       )::integer AS open_alert_count,
                       COUNT(*) FILTER (
                           WHERE severity = 'HIGH'
                             AND alert_status IN (
                                 'OPEN', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION'
                             )
                       )::integer AS high_alert_count,
                       COUNT(*) FILTER (
                           WHERE severity = 'CRITICAL'
                             AND alert_status IN (
                                 'OPEN', 'ACKNOWLEDGED', 'UNDER_INVESTIGATION'
                             )
                       )::integer AS critical_alert_count
                FROM credit.risk_alerts
                WHERE customer_id = :customer_id
                """
            ),
            {"customer_id": customer_id},
        ).mappings().one()

        return {
            "current_credit_score": (
                latest_assessment.get("credit_score") if latest_assessment else None
            ),
            "probability_of_default": (
                latest_assessment.get("probability_of_default")
                if latest_assessment else None
            ),
            "current_risk_band": (
                latest_assessment.get("risk_band") if latest_assessment else None
            ),
            "system_recommendation": (
                latest_assessment.get("system_recommendation")
                if latest_assessment else None
            ),
            "latest_assessment_at": (
                latest_assessment.get("assessment_timestamp")
                if latest_assessment else None
            ),
            "bureau_score": latest_bureau.get("bureau_score") if latest_bureau else None,
            "bureau_max_dpd_12m": (
                latest_bureau.get("max_days_past_due_12m")
                if latest_bureau else None
            ),
            "bureau_delinquent_facilities": (
                latest_bureau.get("delinquent_facilities", 0)
                if latest_bureau else 0
            ),
            "bureau_written_off_facilities": (
                latest_bureau.get("written_off_facilities", 0)
                if latest_bureau else 0
            ),
            "bureau_legal_cases": (
                latest_bureau.get("legal_cases", 0) if latest_bureau else 0
            ),
            "adverse_listing_flag": bool(
                latest_bureau.get("adverse_listing_flag", False)
                if latest_bureau else False
            ),
            **dict(alert_summary),
            "latest_assessment": latest_assessment,
            "latest_bureau_report": latest_bureau,
        }

    def _json_rows(
        self,
        statement: str,
        customer_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        return list(
            self.db.execute(
                text(statement),
                {"customer_id": customer_id, "limit": limit},
            ).scalars().all()
        )

    def get_accounts(self, customer_id: str) -> list[dict[str, Any]]:
        return self._json_rows(
            """
            SELECT to_jsonb(a)
            FROM banking.accounts a
            WHERE a.customer_id = :customer_id
            ORDER BY a.open_date DESC, a.account_id
            LIMIT :limit
            """,
            customer_id,
            100,
        )

    def get_recent_transactions(
        self,
        customer_id: str,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        return self._json_rows(
            """
            SELECT to_jsonb(t)
            FROM banking.account_transactions t
            WHERE t.customer_id = :customer_id
              AND COALESCE(t.reversal_flag, false) = false
            ORDER BY t.posting_timestamp DESC, t.transaction_id
            LIMIT :limit
            """,
            customer_id,
            limit,
        )

    def get_loan_applications(self, customer_id: str) -> list[dict[str, Any]]:
        return self._json_rows(
            """
            SELECT to_jsonb(app)
            FROM credit.loan_applications app
            WHERE app.customer_id = :customer_id
            ORDER BY app.application_date DESC, app.application_id
            LIMIT :limit
            """,
            customer_id,
            100,
        )

    def get_loans(self, customer_id: str) -> list[dict[str, Any]]:
        return self._json_rows(
            """
            SELECT to_jsonb(l)
            FROM banking.loans l
            JOIN credit.loan_applications app
              ON app.application_id = l.application_id
            WHERE app.customer_id = :customer_id
            ORDER BY l.disbursement_date DESC, l.loan_id
            LIMIT :limit
            """,
            customer_id,
            100,
        )

    def get_risk_alerts(self, customer_id: str) -> list[dict[str, Any]]:
        return self._json_rows(
            """
            SELECT to_jsonb(ra)
            FROM credit.risk_alerts ra
            WHERE ra.customer_id = :customer_id
            ORDER BY ra.detected_at DESC, ra.alert_id
            LIMIT :limit
            """,
            customer_id,
            100,
        )

    def get_activity_timeline(self, customer_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            text(
                """
                SELECT event_type, event_timestamp, reference_id, event_status,
                       event_description
                FROM (
                    SELECT 'APPLICATION'::text AS event_type,
                           app.application_date::timestamptz AS event_timestamp,
                           app.application_id::text AS reference_id,
                           app.application_status::text AS event_status,
                           ('Loan application for ' || app.requested_amount::text)
                               AS event_description
                    FROM credit.loan_applications app
                    WHERE app.customer_id = :customer_id

                    UNION ALL

                    SELECT 'ASSESSMENT', ca.assessment_timestamp,
                           ca.assessment_id::text, ca.risk_band,
                           ('Credit score ' || ca.credit_score::text ||
                            ', PD ' || ca.probability_of_default::text)
                    FROM credit.credit_assessments ca
                    JOIN credit.loan_applications app
                      ON app.application_id = ca.application_id
                    WHERE app.customer_id = :customer_id

                    UNION ALL

                    SELECT 'LOAN', l.disbursement_date::timestamptz,
                           l.loan_id::text, l.loan_status,
                           ('Loan disbursed: ' || l.original_principal::text)
                    FROM banking.loans l
                    JOIN credit.loan_applications app
                      ON app.application_id = l.application_id
                    WHERE app.customer_id = :customer_id

                    UNION ALL

                    SELECT 'RISK_ALERT', ra.detected_at,
                           ra.alert_id::text, ra.alert_status,
                           (ra.alert_type || ' - ' || ra.severity)
                    FROM credit.risk_alerts ra
                    WHERE ra.customer_id = :customer_id
                ) events
                WHERE event_timestamp IS NOT NULL
                ORDER BY event_timestamp DESC
                LIMIT 50
                """
            ),
            {"customer_id": customer_id},
        ).mappings().all()
        return [dict(row) for row in rows]

    def create(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
