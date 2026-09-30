from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TransactionOverview(BaseModel):
    date_from: date
    date_to: date
    transaction_count: int
    total_credits: Decimal
    total_debits: Decimal
    net_cash_flow: Decimal
    average_transaction_amount: Decimal
    cash_transaction_count: int
    high_value_transaction_count: int
    active_customer_count: int


class TransactionTrendPoint(BaseModel):
    period: date
    credits: Decimal
    debits: Decimal
    net_cash_flow: Decimal
    transaction_count: int


class TransactionBreakdownItem(BaseModel):
    code: str
    transaction_count: int
    total_amount: Decimal
    percentage: Decimal


class TransactionItem(BaseModel):
    transaction_id: str
    account_id: str
    customer_id: str
    customer_name: str
    posting_timestamp: datetime
    transaction_category: str
    credit_debit_indicator: str
    local_currency_amount: Decimal
    currency_code: str
    channel_code: str
    transaction_description: Optional[str] = None
    cash_transaction_flag: bool
    high_value_flag: bool


class TransactionListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: list[TransactionItem]


class TransactionAnalyticsResponse(BaseModel):
    overview: TransactionOverview
    trend: list[TransactionTrendPoint]
    categories: list[TransactionBreakdownItem]
    channels: list[TransactionBreakdownItem]
