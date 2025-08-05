"""
帳號管理相關 API 路由
處理帳號的 CRUD 操作
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from api.models import (
    AccountCreate, AccountUpdate, AccountResponse, 
    ApiResponse, PaginatedResponse, SiteType
)
from api.auth import get_current_user
import mysql.connector
from config import DB_CONFIG
from datetime import datetime

router = APIRouter()

def get_db_connection():
    """獲取資料庫連接"""
    return mysql.connector.connect(**DB_CONFIG)

@router.get("/", response_model=PaginatedResponse, summary="獲取帳號列表")
async def get_accounts(
    limit: int = Query(50, le=500, description="查詢筆數限制"),
    offset: int = Query(0, ge=0, description="查詢偏移量"),
    site_type: Optional[SiteType] = Query(None, description="網站類型篩選"),
    status: Optional[int] = Query(None, description="狀態篩選"),
    current_user: dict = Depends(get_current_user)
):
    """獲取帳號列表，支援分頁和篩選"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 建立查詢條件
        where_conditions = []
        params = []
        
        if site_type:
            where_conditions.append("account_type = %s")
            params.append(site_type.value)
        
        if status is not None:
            where_conditions.append("status = %s")
            params.append(status)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查詢總數
        count_query = f"SELECT COUNT(*) as total FROM accounts {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        
        # 查詢資料
        data_query = f"""
            SELECT id, account, account_type, status, created_at, updated_at 
            FROM accounts {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [limit, offset])
        accounts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 轉換日期格式
        for account in accounts:
            if account["created_at"]:
                account["created_at"] = account["created_at"].isoformat()
            if account["updated_at"]:
                account["updated_at"] = account["updated_at"].isoformat()
        
        return PaginatedResponse(
            success=True,
            message="成功獲取帳號列表",
            data=accounts,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取帳號列表失敗: {str(e)}"
        )

@router.get("/{account_id}", response_model=ApiResponse, summary="獲取單一帳號")
async def get_account(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """根據 ID 獲取單一帳號資訊"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT id, account, account_type, status, created_at, updated_at FROM accounts WHERE id = %s",
            (account_id,)
        )
        account = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帳號不存在"
            )
        
        # 轉換日期格式
        if account["created_at"]:
            account["created_at"] = account["created_at"].isoformat()
        if account["updated_at"]:
            account["updated_at"] = account["updated_at"].isoformat()
        
        return ApiResponse(
            success=True,
            message="成功獲取帳號資訊",
            data=account
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取帳號資訊失敗: {str(e)}"
        )

@router.post("/", response_model=ApiResponse, summary="建立新帳號")
async def create_account(
    account_data: AccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """建立新的登入帳號"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查帳號是否已存在
        cursor.execute(
            "SELECT id FROM accounts WHERE account = %s AND account_type = %s",
            (account_data.account, account_data.account_type.value)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="該網站的帳號已存在"
            )
        
        # 插入新帳號
        cursor.execute("""
            INSERT INTO accounts (account, password, account_type, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            account_data.account,
            account_data.password,
            account_data.account_type.value,
            account_data.status,
            datetime.now()
        ))
        
        account_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return ApiResponse(
            success=True,
            message="成功建立帳號",
            data={"id": account_id, "account": account_data.account}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立帳號失敗: {str(e)}"
        )

@router.put("/{account_id}", response_model=ApiResponse, summary="更新帳號")
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新現有帳號資訊"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查帳號是否存在
        cursor.execute("SELECT id FROM accounts WHERE id = %s", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帳號不存在"
            )
        
        # 建立更新欄位和參數
        update_fields = []
        params = []
        
        if account_data.password is not None:
            update_fields.append("password = %s")
            params.append(account_data.password)
        
        if account_data.account_type is not None:
            update_fields.append("account_type = %s")
            params.append(account_data.account_type.value)
        
        if account_data.status is not None:
            update_fields.append("status = %s")
            params.append(account_data.status)
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="沒有提供要更新的欄位"
            )
        
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        params.append(account_id)
        
        # 執行更新
        update_query = f"UPDATE accounts SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(update_query, params)
        conn.commit()
        cursor.close()
        conn.close()
        
        return ApiResponse(
            success=True,
            message="成功更新帳號",
            data={"id": account_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新帳號失敗: {str(e)}"
        )

@router.delete("/{account_id}", response_model=ApiResponse, summary="刪除帳號")
async def delete_account(
    account_id: int,
    current_user: dict = Depends(get_current_user)
):
    """刪除帳號（軟刪除，設定狀態為 0）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查帳號是否存在
        cursor.execute("SELECT id FROM accounts WHERE id = %s", (account_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帳號不存在"
            )
        
        # 軟刪除（設定狀態為 0）
        cursor.execute(
            "UPDATE accounts SET status = 0, updated_at = %s WHERE id = %s",
            (datetime.now(), account_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return ApiResponse(
            success=True,
            message="成功刪除帳號",
            data={"id": account_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除帳號失敗: {str(e)}"
        )
