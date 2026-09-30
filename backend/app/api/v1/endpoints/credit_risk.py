from typing import Optional, List
from typing_extensions import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.credit_risk import (
    AssessmentListResponse,
    CreditRiskAssessmentResponse,
    CreditRiskModelResponse,
    PortfolioDistributionResponse,
    PortfolioSummaryResponse,
    RecentScoringItem,
)
from backend.app.services.credit_risk_service import (
    ApplicationNotFoundError,
    AssessmentNotFoundError,
    CreditRiskService,
)


router = APIRouter(
    prefix="/credit-risk",
    tags=["Credit Risk"],
)


@router.post(
    "/applications/{application_id}/score",
    response_model=CreditRiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Score an MSME loan application",
)
def score_application(
    application_id: str,
    database: Session = Depends(get_db),
    x_user_id: Annotated[Optional[UUID], Header()] = None,
) -> CreditRiskAssessmentResponse:
    try:
        result = CreditRiskService(database).score_application(
            application_id=application_id,
            created_by=x_user_id,
        )
        return CreditRiskAssessmentResponse(**result)
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} was not found in the scoring view",
        ) from exc
    except SQLAlchemyError as exc:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assessment could not be saved",
        ) from exc


@router.get(
    "/applications/{application_id}/latest",
    response_model=CreditRiskAssessmentResponse,
    summary="Get the latest assessment for an application",
)
def latest_assessment(
    application_id: str,
    database: Session = Depends(get_db),
) -> CreditRiskAssessmentResponse:
    try:
        result = CreditRiskService(database).latest_assessment(application_id)
        return CreditRiskAssessmentResponse(**result)
    except AssessmentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment exists for application {application_id}",
        ) from exc


@router.get(
    "/model",
    response_model=CreditRiskModelResponse,
    summary="Get champion credit-risk model information",
)
def model_info(
    database: Session = Depends(get_db),
) -> CreditRiskModelResponse:
    result = CreditRiskService(database).model_info()
    return CreditRiskModelResponse(**result)


@router.get(
    "/portfolio/summary",
    response_model=PortfolioSummaryResponse,
    summary="Get portfolio credit-risk summary",
)
def portfolio_summary(
    database: Session = Depends(get_db),
) -> PortfolioSummaryResponse:
    result = CreditRiskService(database).portfolio_summary()
    return PortfolioSummaryResponse(**result)


@router.get(
    "/assessments",
    response_model=AssessmentListResponse,
    summary="List latest application assessments",
)
def list_assessments(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Optional[str] = None,
    risk_band: Annotated[
        Optional[str],
        Query(pattern="^(VERY_LOW|LOW|MEDIUM|HIGH|VERY_HIGH)$"),
    ] = None,
    recommendation: Annotated[
        Optional[str],
        Query(
            pattern=(
                "^(RECOMMEND_APPROVAL|REFER_FOR_APPROVAL|"
                "REQUEST_MORE_INFORMATION|REFER_FOR_ENHANCED_REVIEW|"
                "RECOMMEND_DECLINE)$"
            )
        ),
    ] = None,
    database: Session = Depends(get_db),
) -> AssessmentListResponse:
    result = CreditRiskService(database).list_assessments(
        page=page,
        page_size=page_size,
        search=search,
        risk_band=risk_band,
        recommendation=recommendation,
    )
    return AssessmentListResponse(**result)


@router.get(
    "/review-queue",
    response_model=AssessmentListResponse,
    summary="List applications requiring analyst action",
)
def review_queue(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    database: Session = Depends(get_db),
) -> AssessmentListResponse:
    result = CreditRiskService(database).review_queue(page, page_size)
    return AssessmentListResponse(**result)


@router.get(
    "/portfolio/distribution",
    response_model=PortfolioDistributionResponse,
    summary="Get probability-of-default distribution",
)
def portfolio_distribution(
    database: Session = Depends(get_db),
) -> PortfolioDistributionResponse:
    result = CreditRiskService(database).probability_distribution()
    return PortfolioDistributionResponse(**result)


@router.get(
    "/high-risk-customers",
    response_model=AssessmentListResponse,
    summary="List high and very-high-risk applications",
)
def high_risk_customers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    database: Session = Depends(get_db),
) -> AssessmentListResponse:
    result = CreditRiskService(database).high_risk_customers(page, page_size)
    return AssessmentListResponse(**result)


@router.get(
    "/recent-activity",
    response_model=List[RecentScoringItem],
    summary="Get recent scoring activity",
)
def recent_activity(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    database: Session = Depends(get_db),
) -> List[RecentScoringItem]:
    rows = CreditRiskService(database).recent_activity(limit)
    return [RecentScoringItem(**row) for row in rows]
