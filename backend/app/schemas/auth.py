from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class AuthenticatedUser(BaseModel):
    user_id: UUID
    username: str
    email: str
    full_name: str
    role_code: str
    employee_number: Optional[str] = None
    branch_code: Optional[str] = None
    account_status: str
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: AuthenticatedUser
