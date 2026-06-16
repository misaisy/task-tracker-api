"""
Роутер для пользователей.
Слой: HTTP (routers).
Зависит от: services, models, dependencies.
"""
from fastapi import APIRouter, Depends, status

from app.dependencies import get_user_service
from app.models import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user.model_dump())


@router.get("/", response_model=list[UserResponse])
async def list_users(service: UserService = Depends(get_user_service)):
    return await service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return await service.get_user_by_id(user_id)
