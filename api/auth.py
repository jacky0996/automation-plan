"""
認證和授權模組
處理 JWT Token 認證、密碼加密等
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import mysql.connector
from config import DB_CONFIG

# JWT 設定
from config import JWT_CONFIG
SECRET_KEY = JWT_CONFIG['secret_key']
ALGORITHM = JWT_CONFIG['algorithm']
ACCESS_TOKEN_EXPIRE_MINUTES = JWT_CONFIG['access_token_expire_minutes']

# 密碼加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """加密密碼"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """建立 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """驗證 JWT Token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return {"username": username, "user_id": payload.get("user_id")}
    except JWTError:
        return None

def get_user_from_db(username: str) -> Optional[Dict[str, Any]]:
    """從資料庫獲取使用者資訊"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 這裡假設有一個 users 表，實際專案中可能需要調整
        cursor.execute(
            "SELECT id, username, email, created_at FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return user
    except Exception as e:
        print(f"取得使用者資訊錯誤: {e}")
        return None

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """驗證使用者登入"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 這裡假設有一個 users 表，實際專案中可能需要調整
        cursor.execute(
            "SELECT id, username, password_hash, email, created_at FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and verify_password(password, user["password_hash"]):
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "created_at": user["created_at"]
            }
        return None
    except Exception as e:
        print(f"使用者認證錯誤: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """獲取當前使用者（依賴注入）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效的認證憑證",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user = get_user_from_db(payload["username"])
        if user is None:
            raise credentials_exception
        
        return user
    except Exception:
        raise credentials_exception

# 可選的權限檢查函數
def require_permission(permission: str):
    """權限檢查裝飾器（可擴展使用）"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        # 這裡可以實作具體的權限檢查邏輯
        # 例如檢查使用者角色、權限等
        return current_user
    return permission_checker
