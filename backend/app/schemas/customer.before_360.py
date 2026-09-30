from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator


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
    pass


class CustomerRiskSummary(BaseModel):
    pass


class Customer360Response(BaseModel):
    customer: CustomerProfile
    financial_summary: CustomerFinancialSummary
    risk_summary: CustomerRiskSummary


class CustomerListResponse(BaseModel):
    page: int
    page_size: int
    total_records: int
    total_pages: int
    records: List[CustomerListItem]