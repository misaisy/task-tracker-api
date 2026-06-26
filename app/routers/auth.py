from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import get_user_service
from app.dependencies.auth import create_access_token
from app.models.schemas import UserRegisterRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Вход по имени и паролю. Возвращает JWT-токен."""
    user = await user_service.authenticate(form_data.username, form_data.password)
    token = await create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.create_user(request.model_dump(mode='json'))
