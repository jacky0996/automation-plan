"""
Pydantic 模型定義
用於 API 請求和回應的資料結構
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SiteType(str, Enum):
    """支援的網站類型"""
    PTT = "PTT"
    CMONEY = "CMONEY"

class TaskStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class LoginStatus(str, Enum):
    """登入狀態"""
    SUCCESS = "成功"
    FAILED = "失敗"

# 認證相關模型
class LoginRequest(BaseModel):
    """登入請求"""
    username: str = Field(..., description="使用者名稱")
    password: str = Field(..., description="密碼")

class Token(BaseModel):
    """JWT Token"""
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    """使用者資訊回應"""
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

# 帳號管理相關模型
class AccountCreate(BaseModel):
    """建立帳號請求"""
    account: str = Field(..., description="帳號名稱")
    password: str = Field(..., description="密碼")
    account_type: SiteType = Field(..., description="網站類型")
    status: int = Field(default=1, description="帳號狀態 (0:停用, 1:啟用)")

class AccountUpdate(BaseModel):
    """更新帳號請求"""
    password: Optional[str] = Field(None, description="密碼")
    account_type: Optional[SiteType] = Field(None, description="網站類型")
    status: Optional[int] = Field(None, description="帳號狀態")

class AccountResponse(BaseModel):
    """帳號資訊回應"""
    id: int
    account: str
    account_type: str
    status: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# 任務管理相關模型
class TaskCreate(BaseModel):
    """建立任務請求"""
    site_type: SiteType = Field(..., description="網站類型")
    account_ids: List[int] = Field(..., description="帳號ID列表")
    task_type: str = Field(default="login", description="任務類型")

class TaskResponse(BaseModel):
    """任務回應"""
    id: str = Field(..., description="任務ID")
    status: TaskStatus = Field(..., description="任務狀態")
    site_type: str = Field(..., description="網站類型")
    account_count: int = Field(..., description="處理帳號數量")
    created_at: datetime = Field(..., description="建立時間")
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

# 日誌查詢相關模型
class LoginLogResponse(BaseModel):
    """登入日誌回應"""
    id: int
    account_id: int
    account_name: str
    site_name: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    status: str
    message: Optional[str] = None

class LoginLogQuery(BaseModel):
    """登入日誌查詢參數"""
    account_id: Optional[int] = None
    site_name: Optional[str] = None
    status: Optional[LoginStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=500, description="查詢筆數限制")
    offset: int = Field(default=0, ge=0, description="查詢偏移量")

# 統計相關模型
class DashboardStats(BaseModel):
    """儀表板統計資料"""
    total_accounts: int
    active_accounts: int
    inactive_accounts: int
    ptt_accounts: int
    cmoney_accounts: int
    today_logins: int
    today_failures: int
    pending_tasks: int

# 通用回應模型
class ApiResponse(BaseModel):
    """API 通用回應格式"""
    success: bool
    message: str
    data: Optional[Any] = None
    
class PaginatedResponse(BaseModel):
    """分頁回應格式"""
    success: bool
    message: str
    data: List[Any]
    total: int
    limit: int
    offset: int
    has_next: bool
