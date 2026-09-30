from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, verify_password
from backend.app.repositories.auth_repository import AuthRepository
from backend.app.schemas.auth import AuthenticatedUser, LoginResponse


class AuthService:
    def __init__(self, database: Session) -> None:
        self.database = database
        self.repository = AuthRepository(database)

    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
    ) -> LoginResponse:
        record = self.repository.find_by_username(username)
        if record is None:
            raise self._invalid_credentials()

        user_id = UUID(str(record["user_id"]))
        if record["account_status"] != "ACTIVE":
            self.repository.add_audit(
                user_id=user_id,
                action="LOGIN_BLOCKED",
                entity_id=str(user_id),
                reason=f"Login blocked because account status is {record['account_status']}",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.database.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked or disabled")

        if not verify_password(password, record["password_hash"]):
            attempts = int(record["failed_login_attempts"] or 0) + 1
            locked = attempts >= settings.auth_max_failed_attempts
            self.repository.record_failed_login(user_id, attempts, locked)
            self.repository.add_audit(
                user_id=user_id,
                action="LOGIN_FAILED",
                entity_id=str(user_id),
                reason="Invalid password",
                ip_address=ip_address,
                user_agent=user_agent,
                new_value={"failed_login_attempts": attempts, "locked": locked},
            )
            self.database.commit()
            if locked:
                raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked after repeated failed login attempts")
            raise self._invalid_credentials()

        authenticated = self.repository.record_successful_login(user_id)
        self.repository.add_audit(
            user_id=user_id,
            action="LOGIN_SUCCESS",
            entity_id=str(user_id),
            reason="Successful portal login",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.database.commit()

        user = AuthenticatedUser(**authenticated)
        token, expires_in = create_access_token(
            subject=str(user.user_id),
            username=user.username,
            role_code=user.role_code,
        )
        return LoginResponse(access_token=token, expires_in=expires_in, user=user)

    @staticmethod
    def _invalid_credentials() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
