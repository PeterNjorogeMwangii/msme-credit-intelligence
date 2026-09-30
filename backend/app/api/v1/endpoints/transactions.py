from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.transactions import TransactionAnalyticsResponse, TransactionListResponse
from backend.app.services.transaction_service import TransactionService


router = APIRouter(prefix="/transactions", tags=["Transaction Analytics"])


def common_filters(
    days: Annotated[int, Query(ge=1, le=730)] = 180,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[str] = None,
    account_id: Optional[str] = None,
    direction: Annotated[Optional[str], Query(pattern="^(C|D)$")] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    search: Optional[str] = None,
    high_value_only: bool = False,
) -> dict:
    return {
        "days": days, "date_from": date_from, "date_to": date_to,
        "customer_id": customer_id, "account_id": account_id,
        "direction": direction, "category": category, "channel": channel,
        "search": search, "high_value_only": high_value_only,
    }


@router.get("/analytics", response_model=TransactionAnalyticsResponse)
def analytics(filters: Annotated[dict, Depends(common_filters)], database: Session = Depends(get_db)):
    return TransactionService(database).analytics(**filters)


@router.get("", response_model=TransactionListResponse)
def transactions(
    filters: Annotated[dict, Depends(common_filters)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    database: Session = Depends(get_db),
):
    return TransactionService(database).transactions(page=page, page_size=page_size, **filters)


@router.get("/export.csv")
def export_csv(filters: Annotated[dict, Depends(common_filters)], database: Session = Depends(get_db)):
    content = TransactionService(database).csv_export(**filters)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=transaction_analytics.csv"},
    )
