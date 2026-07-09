from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.presentation.schemas import UserRegister, TokenResponse, UserResponse
from src.presentation.api.dependencies import get_user_use_cases

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, use_cases = Depends(get_user_use_cases)):
    register_uc, _ = use_cases
    try:
        user = register_uc.execute(user_in.email, user_in.password, user_in.role)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), use_cases = Depends(get_user_use_cases)):
    _, auth_uc = use_cases
    try:
        access_token, refresh_token = auth_uc.execute(form_data.username, form_data.password)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
