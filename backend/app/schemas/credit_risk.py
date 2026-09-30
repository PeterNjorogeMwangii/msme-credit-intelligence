from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class CreditRiskAssessmentResponse(BaseModel):
    assessment_id: UUID
    application_id: str
    assessment_version: int
    assessment_timestamp: datetime
    model_name: str
    model_version: str
    credit_score: int = Field(ge=300, le=850)
    probability_of_default: float = Field(ge=0, le=1)
    risk_band: str
    monthly_repayment_capacity: float = Field(ge=0)
    debt_service_ratio: Optional[float] = Field(default=None, ge=0)
    recommended_loan_limit: float = Field(ge=0)
    recommended_term_months: Optional[int] = Field(default=None, gt=0)
    system_recommendation: str
    positive_factors: list[Union[str, dict[str, Any]]]
    negative_factors: list[Union[str, dict[str, Any]]]
    policy_results: dict[str, Any]
    data_completeness_score: float = Field(ge=0, le=100)
    created_at: datetime


class CreditRiskModelResponse(BaseModel):
    model_name: str
    model_version: str
    feature_count: int
    decision_threshold: float
    risk_bands: dict[str, str]
    artifact_path: str


class RiskBandSummary(BaseModel):
    risk_band: str
    application_count: int
    percentage: float
    average_probability_of_default: float


class PortfolioSummaryResponse(BaseModel):
    total_assessed_applications: int
    average_credit_score: float
    average_probability_of_default: float
    high_risk_applications: int
    review_queue_count: int
    risk_bands: list[RiskBandSummary]


class AssessmentListItem(BaseModel):
    assessment_id: UUID
    application_id: str
    customer_id: str
    business_name: str
    requested_amount: float
    application_status: str
    assessment_version: int
    assessment_timestamp: datetime
    credit_score: int
    probability_of_default: float
    risk_band: str
    system_recommendation: str
    recommended_loan_limit: float


class AssessmentListResponse(BaseModel):
    items: list[AssessmentListItem]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ProbabilityBucket(BaseModel):
    bucket: str
    lower_bound: float
    upper_bound: float
    application_count: int
    percentage: float


class PortfolioDistributionResponse(BaseModel):
    total_applications: int
    buckets: list[ProbabilityBucket]


class RecentScoringItem(BaseModel):
    assessment_id: UUID
    application_id: str
    customer_id: str
    business_name: str
    assessment_timestamp: datetime
    credit_score: int
    probability_of_default: float
    risk_band: str
    system_recommendation: str
