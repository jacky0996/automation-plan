"""
認證相關 API 路由
處理登入、登出、Token 更新等
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from api.models import LoginRequest, Token, ApiResponse
from api.auth import authenticate_user, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/login", response_model=Token, summary="使用者登入")
async def login(login_request: LoginRequest):
    """
    使用者登入
    - **username**: 使用者名稱
    - **password**: 密碼
    """
    user = authenticate_user(login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", summary="獲取當前使用者資訊")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """獲取當前登入使用者的資訊"""
    return ApiResponse(
        success=True,
        message="成功獲取使用者資訊",
        data={
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user.get("email"),
            "created_at": current_user["created_at"].isoformat() if current_user["created_at"] else None
        }
    )

@router.post("/logout", summary="使用者登出")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    使用者登出
    由於使用 JWT，實際上是前端刪除 Token
    """
    return ApiResponse(
        success=True,
        message="登出成功",
        data={"username": current_user["username"]}
    )

@router.post("/refresh", summary="刷新 Token")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """刷新 JWT Token"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["username"], "user_id": current_user["id"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
