from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.controllers.user_controller import UserController
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import create_access_token, get_current_user
from datetime import timedelta

router = APIRouter()
controller = UserController()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    return await controller.create_user(user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await controller.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: str = Depends(get_current_user)):
    user = await controller.get_user_by_email(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user 