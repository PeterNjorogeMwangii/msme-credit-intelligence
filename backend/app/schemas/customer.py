from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    customer_number: Optional[str] = None
    customer_type: Optional[str] = None
    legal_name: Optional[str] = None
    trading_name: Optional[str] = None
    registration_number: Optional[str] = None
    tax_identifier: Optional[str] = None
    business_type: Optional[str] = None
    industry_code: Optional[str] = None
    industry_description: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    relationship_start_date: Optional[datetime] = None
    employee_count: Optional[int] = None
    annual_turnover_declared: Optional[Decimal] = None
    turnover_currency: Optional[str] = None
    county_code: Optional[str] = None
    branch_code: Optional[str] = None
    relationship_manager_id: Optional[str] = None
    kyc_status: Optional[str] = None
    kyc_review_date: Optional[datetime] = None
    aml_risk_classification: Optional[str] = None
    pep_flag: Optional[bool] = None
    sanctions_match_flag: Optional[bool] = None
    record_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    legal_name: Optional[str] = None
    trading_name: Optional[str] = None
    record_status: Optional[str] = None
    aml_risk_classification: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CustomerFinancialSummary(BaseModel):
    account_count: int = 0
    active_account_count: int = 0
    estimated_total_balance: Decimal = Decimal("0")
    transaction_count_180d: int = 0
    total_credits_180d: Decimal = Decimal("0")
    total_debits_180d: Decimal = Decimal("0")
    net_cash_flow_180d: Decimal = Decimal("0")
    average_transaction_amount_180d: Decimal = Decimal("0")
    cash_transaction_count_180d: int = 0
    application_count: int = 0
    approved_application_count: int = 0
    declined_application_count: int = 0
    total_requested_amount: Decimal = Decimal("0")
    loan_count: int = 0
    active_loan_count: int = 0
    total_original_principal: Decimal = Decimal("0")
    total_outstanding_principal: Decimal = Decimal("0")
    total_arrears: Decimal = Decimal("0")
    maximum_days_past_due: int = 0
    scheduled_installment_count: int = 0
    overdue_installment_count: int = 0
    scheduled_amount_due: Decimal = Decimal("0")
    scheduled_amount_paid: Decimal = Decimal("0")
    scheduled_outstanding_amount: Decimal = Decimal("0")


class CustomerRiskSummary(BaseModel):
    current_credit_score: Optional[int] = None
    probability_of_default: Optional[Decimal] = None
    current_risk_band: Optional[str] = None
    system_recommendation: Optional[str] = None
    latest_assessment_at: Optional[datetime] = None
    bureau_score: Optional[int] = None
    bureau_max_dpd_12m: Optional[int] = None
    bureau_delinquent_facilities: int = 0
    bureau_written_off_facilities: int = 0
    bureau_legal_cases: int = 0
    adverse_listing_flag: bool = False
    open_alert_count: int = 0
    high_alert_count: int = 0
    critical_alert_count: int = 0
    latest_assessment: Optional[dict[str, Any]] = None
    latest_bureau_report: Optional[dict[str, Any]] = None


class Customer360Response(BaseModel):
    customer: CustomerProfile
    financial_summary: CustomerFinancialSummary
    risk_summary: CustomerRiskSummary
    accounts: list[dict[str, Any]] = Field(default_factory=list)
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    loan_applications: list[dict[str, Any]] = Field(default_factory=list)
    loans: list[dict[str, Any]] = Field(default_factory=list)
    risk_alerts: list[dict[str, Any]] = Field(default_factory=list)
    activity_timeline: list[dict[str, Any]] = Field(default_factory=list)


class CustomerListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: List[CustomerListItem]
