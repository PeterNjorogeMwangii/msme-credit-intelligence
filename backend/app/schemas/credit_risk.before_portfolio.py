from datetime import datetime
from typing import Any, Optional
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
    positive_factors: list[dict[str, Any]]
    negative_factors: list[dict[str, Any]]
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
