from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.credit_risk import (
    CreditRiskAssessmentResponse,
    CreditRiskModelResponse,
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
