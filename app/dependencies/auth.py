from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.constants import Role
from app.core.settings import settings
from app.dependencies.services import get_task_service, get_user_service
from app.errors.exceptions import TaskNotFoundError, UserNotFoundError
from app.models.orm import Task, User
from app.services.task_service import TaskService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(user_id: UUID) -> str:
    """Создаёт JWT-токен для пользователя."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM])
        user_id = payload.get("sub")
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    try:
        user_id = UUID(user_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    try:
        user = await user_service.get_user_by_id(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from e

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_owner_or_admin(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> Task:
    try:
        task = await task_service.get_task_by_id(task_id)
    except TaskNotFoundError as e:
        raise e

    if task.owner_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return task
