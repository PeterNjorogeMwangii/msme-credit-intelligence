from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.api.dependencies.auth import get_current_user
from backend.app.database.session import get_db
from backend.app.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse
from backend.app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, database: Session = Depends(get_db)) -> LoginResponse:
    return AuthService(database).login(
        username=payload.username,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/me", response_model=AuthenticatedUser)
def me(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
    return current_user
