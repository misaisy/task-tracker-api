"""
Роутер для пользователей.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_user_service, require_admin
from app.models.orm import User
from app.models.schemas import UpdateUserRoleRequest, UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
    admin: User = Depends(require_admin),
):
    return await service.create_user(user.model_dump(mode='json'))


@router.get("/", response_model=list[UserResponse])
async def list_users(service: UserService = Depends(get_user_service)):
    return await service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    return await service.get_user_by_id(user_id)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    service: UserService = Depends(get_user_service),
    admin: User = Depends(require_admin),
):
    """Повышает или понижает роль пользователя. Только для админов."""
    return await service.update_user_role(user_id, request.role)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    require_admin: User = Depends(require_admin),
):
    return await service.deactivate_user(user_id)
