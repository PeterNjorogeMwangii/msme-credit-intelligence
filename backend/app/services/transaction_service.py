import csv
import io
import math
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.repositories.transaction_repository import TransactionRepository
from backend.app.schemas.transactions import (
    TransactionAnalyticsResponse,
    TransactionBreakdownItem,
    TransactionListResponse,
    TransactionOverview,
    TransactionTrendPoint,
)


class TransactionService:
    def __init__(self, database: Session) -> None:
        self.repository = TransactionRepository(database)

    def query(
        self,
        *,
        days: int,
        date_from: Optional[date],
        date_to: Optional[date],
        **filters: Any,
    ):
        resolved_from, resolved_to = self.repository.resolve_period(days, date_from, date_to)
        where, parameters = self.repository.filters(
            date_from=resolved_from, date_to=resolved_to, **filters
        )
        return resolved_from, resolved_to, where, parameters

    def analytics(
        self,
        *,
        days: int,
        date_from: Optional[date],
        date_to: Optional[date],
        **filters: Any,
    ) -> TransactionAnalyticsResponse:
        resolved_from, resolved_to, where, parameters = self.query(
            days=days, date_from=date_from, date_to=date_to, **filters
        )
        overview = self.repository.overview(where, parameters)
        overview.update(date_from=resolved_from, date_to=resolved_to)
        return TransactionAnalyticsResponse(
            overview=TransactionOverview(**overview),
            trend=[TransactionTrendPoint(**row) for row in self.repository.trend(where, parameters)],
            categories=[
                TransactionBreakdownItem(**row)
                for row in self.repository.breakdown("t.transaction_category", where, parameters)
            ],
            channels=[
                TransactionBreakdownItem(**row)
                for row in self.repository.breakdown("t.channel_code", where, parameters, 10)
            ],
        )

    def transactions(
        self,
        *,
        page: int,
        page_size: int,
        days: int,
        date_from: Optional[date],
        date_to: Optional[date],
        **filters: Any,
    ) -> TransactionListResponse:
        _, _, where, parameters = self.query(days=days, date_from=date_from, date_to=date_to, **filters)
        total = self.repository.count(where, parameters)
        return TransactionListResponse(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=math.ceil(total / page_size) if total else 0,
            records=self.repository.list(where, parameters, (page - 1) * page_size, page_size),
        )

    def csv_export(
        self,
        *,
        days: int,
        date_from: Optional[date],
        date_to: Optional[date],
        **filters: Any,
    ) -> str:
        _, _, where, parameters = self.query(days=days, date_from=date_from, date_to=date_to, **filters)
        rows = self.repository.export(where, parameters)
        output = io.StringIO()
        fieldnames = list(rows[0].keys()) if rows else [
            "transaction_id", "account_id", "customer_id", "customer_name",
            "posting_timestamp", "value_date", "transaction_category",
            "credit_debit_indicator", "local_currency_amount", "currency_code",
            "channel_code", "transaction_description", "reference_number",
            "cash_transaction_flag",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()
