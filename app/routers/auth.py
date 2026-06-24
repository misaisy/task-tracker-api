from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import create_access_token
from app.dependencies.db import get_db
from app.storage.user_store import UserStore

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(username: str, db: AsyncSession = Depends(get_db)):
    """Вход по username. Возвращает JWT-токен."""
    user_store = UserStore(db)
    user = await user_store.get_by_username(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
