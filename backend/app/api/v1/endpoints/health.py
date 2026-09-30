from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.schemas.health import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API and database health",
)
def health_check(
    database: Session = Depends(get_db),
) -> HealthResponse:
    try:
        result = database.execute(
            text(
                """
                SELECT
                    current_database(),
                    current_user
                """
            )
        ).one()

        database_name = result[0]
        database_user = result[1]

        database.execute(text("SELECT 1"))

        return HealthResponse(
            status="healthy",
            application=settings.app_name,
            version=settings.app_version,
            environment=settings.app_environment,
            database=database_name,
            database_user=database_user,
        )

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable.",
        ) from error