from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session


HIGH_VALUE_THRESHOLD = 100_000


class TransactionRepository:
    def __init__(self, database: Session) -> None:
        self.database = database

    def resolve_period(
        self,
        days: int,
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> Tuple[date, date]:
        maximum = self.database.execute(
            text("SELECT MAX(value_date) FROM banking.account_transactions")
        ).scalar_one_or_none()
        resolved_to = date_to or maximum or date.today()
        resolved_from = date_from or (resolved_to - timedelta(days=days - 1))
        return resolved_from, resolved_to

    @staticmethod
    def filters(
        *,
        date_from: date,
        date_to: date,
        customer_id: Optional[str] = None,
        account_id: Optional[str] = None,
        direction: Optional[str] = None,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        search: Optional[str] = None,
        high_value_only: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        clauses = [
            "t.value_date BETWEEN :date_from AND :date_to",
            "COALESCE(t.reversal_flag, false) = false",
        ]
        parameters: Dict[str, Any] = {"date_from": date_from, "date_to": date_to}

        filters_map = {
            "customer_id": ("t.customer_id", customer_id),
            "account_id": ("t.account_id", account_id),
            "direction": ("t.credit_debit_indicator", direction),
            "category": ("t.transaction_category", category),
            "channel": ("t.channel_code", channel),
        }

        for key, (column, value) in filters_map.items():
            if value:
                clauses.append(f"{column} = :{key}")
                parameters[key] = value

        if search:
            clauses.append(
                "(t.transaction_id ILIKE :search OR t.transaction_description ILIKE :search OR c.legal_name ILIKE :search OR t.customer_id ILIKE :search)"
            )
            parameters["search"] = f"%{search.strip()}%"

        if high_value_only:
            clauses.append("t.local_currency_amount >= :high_value_threshold")
            parameters["high_value_threshold"] = HIGH_VALUE_THRESHOLD

        return " AND ".join(clauses), parameters

    def overview(self, where: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        row = self.database.execute(
            text(f"""
                SELECT COUNT(*) AS transaction_count,
                       COALESCE(SUM(t.local_currency_amount) FILTER (WHERE t.credit_debit_indicator = 'C'), 0) AS total_credits,
                       COALESCE(SUM(t.local_currency_amount) FILTER (WHERE t.credit_debit_indicator = 'D'), 0) AS total_debits,
                       COALESCE(SUM(CASE WHEN t.credit_debit_indicator = 'C' THEN t.local_currency_amount ELSE -t.local_currency_amount END), 0) AS net_cash_flow,
                       COALESCE(AVG(t.local_currency_amount), 0) AS average_transaction_amount,
                       COUNT(*) FILTER (WHERE t.cash_transaction_flag = true) AS cash_transaction_count,
                       COUNT(*) FILTER (WHERE t.local_currency_amount >= :high_value_threshold) AS high_value_transaction_count,
                       COUNT(DISTINCT t.customer_id) AS active_customer_count
                  FROM banking.account_transactions t
                  JOIN banking.customers c ON c.customer_id = t.customer_id
                 WHERE {where}
            """),
            {**parameters, "high_value_threshold": HIGH_VALUE_THRESHOLD},
        ).mappings().one()
        return dict(row)

    def trend(self, where: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows = self.database.execute(
            text(f"""
                SELECT date_trunc('month', t.value_date)::date AS period,
                       COALESCE(SUM(t.local_currency_amount) FILTER (WHERE t.credit_debit_indicator = 'C'), 0) AS credits,
                       COALESCE(SUM(t.local_currency_amount) FILTER (WHERE t.credit_debit_indicator = 'D'), 0) AS debits,
                       COALESCE(SUM(CASE WHEN t.credit_debit_indicator = 'C' THEN t.local_currency_amount ELSE -t.local_currency_amount END), 0) AS net_cash_flow,
                       COUNT(*) AS transaction_count
                  FROM banking.account_transactions t
                  JOIN banking.customers c ON c.customer_id = t.customer_id
                 WHERE {where}
                 GROUP BY 1 ORDER BY 1
            """), parameters
        ).mappings().all()
        return [dict(row) for row in rows]

    def breakdown(
        self,
        column: str,
        where: str,
        parameters: Dict[str, Any],
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        rows = self.database.execute(
            text(f"""
                WITH grouped AS (
                    SELECT COALESCE({column}, 'UNKNOWN') AS code,
                           COUNT(*) AS transaction_count,
                           SUM(t.local_currency_amount) AS total_amount
                      FROM banking.account_transactions t
                      JOIN banking.customers c ON c.customer_id = t.customer_id
                     WHERE {where}
                     GROUP BY 1
                )
                SELECT code, transaction_count, total_amount,
                       ROUND(100.0 * transaction_count / NULLIF(SUM(transaction_count) OVER (), 0), 2) AS percentage
                  FROM grouped
                  ORDER BY total_amount DESC
                  LIMIT :breakdown_limit
            """), {**parameters, "breakdown_limit": limit}
        ).mappings().all()
        return [dict(row) for row in rows]

    def count(self, where: str, parameters: Dict[str, Any]) -> int:
        return int(
            self.database.execute(
                text(f"""
                    SELECT COUNT(*)
                      FROM banking.account_transactions t
                      JOIN banking.customers c ON c.customer_id = t.customer_id
                     WHERE {where}
                """), parameters
            ).scalar_one()
        )

    def list(self, where: str, parameters: Dict[str, Any], offset: int, limit: int) -> List[Dict[str, Any]]:
        rows = self.database.execute(
            text(f"""
                SELECT t.transaction_id, t.account_id, t.customer_id,
                       c.legal_name AS customer_name, t.posting_timestamp,
                       t.transaction_category, t.credit_debit_indicator,
                       t.local_currency_amount, t.currency_code, t.channel_code,
                       t.transaction_description, t.cash_transaction_flag,
                       (t.local_currency_amount >= :high_value_threshold) AS high_value_flag
                  FROM banking.account_transactions t
                  JOIN banking.customers c ON c.customer_id = t.customer_id
                 WHERE {where}
                 ORDER BY t.posting_timestamp DESC, t.transaction_id
                 LIMIT :limit OFFSET :offset
            """), {**parameters, "limit": limit, "offset": offset, "high_value_threshold": HIGH_VALUE_THRESHOLD}
        ).mappings().all()
        return [dict(row) for row in rows]

    def export(self, where: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows = self.database.execute(
            text(f"""
                SELECT t.transaction_id, t.account_id, t.customer_id, c.legal_name AS customer_name,
                       t.posting_timestamp, t.value_date, t.transaction_category,
                       t.credit_debit_indicator, t.local_currency_amount, t.currency_code,
                       t.channel_code, t.transaction_description, t.reference_number,
                       t.cash_transaction_flag
                  FROM banking.account_transactions t
                  JOIN banking.customers c ON c.customer_id = t.customer_id
                 WHERE {where}
                 ORDER BY t.posting_timestamp DESC
            """), parameters
        ).mappings().all()
        return [dict(row) for row in rows]
