"""
日誌查詢相關 API 路由
處理登入日誌、活動記錄的查詢
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from api.models import (
    LoginLogResponse, LoginLogQuery, ApiResponse, 
    PaginatedResponse, DashboardStats, LoginStatus
)
from api.auth import get_current_user
import mysql.connector
from config import DB_CONFIG

router = APIRouter()

def get_db_connection():
    """獲取資料庫連接"""
    return mysql.connector.connect(**DB_CONFIG)

@router.get("/login-logs", response_model=PaginatedResponse, summary="獲取登入日誌")
async def get_login_logs(
    limit: int = Query(50, le=500, description="查詢筆數限制"),
    offset: int = Query(0, ge=0, description="查詢偏移量"),
    account_id: Optional[int] = Query(None, description="帳號ID篩選"),
    site_name: Optional[str] = Query(None, description="網站名稱篩選"),
    status: Optional[LoginStatus] = Query(None, description="狀態篩選"),
    start_date: Optional[datetime] = Query(None, description="開始日期"),
    end_date: Optional[datetime] = Query(None, description="結束日期"),
    current_user: dict = Depends(get_current_user)
):
    """獲取登入日誌列表，支援多種篩選條件"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 建立查詢條件
        where_conditions = []
        params = []
        
        if account_id:
            where_conditions.append("ll.account_id = %s")
            params.append(account_id)
        
        if site_name:
            where_conditions.append("ll.site_name = %s")
            params.append(site_name)
        
        if status:
            where_conditions.append("ll.status = %s")
            params.append(status.value)
        
        if start_date:
            where_conditions.append("ll.login_time >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("ll.login_time <= %s")
            params.append(end_date)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查詢總數
        count_query = f"""
            SELECT COUNT(*) as total 
            FROM login_logs ll 
            INNER JOIN accounts a ON ll.account_id = a.id 
            {where_clause}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        
        # 查詢資料
        data_query = f"""
            SELECT 
                ll.id,
                ll.account_id,
                a.account as account_name,
                ll.site_name,
                ll.login_time,
                ll.logout_time,
                ll.status,
                ll.message
            FROM login_logs ll
            INNER JOIN accounts a ON ll.account_id = a.id
            {where_clause}
            ORDER BY ll.login_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_query, params + [limit, offset])
        logs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 轉換日期格式
        for log in logs:
            if log["login_time"]:
                log["login_time"] = log["login_time"].isoformat()
            if log["logout_time"]:
                log["logout_time"] = log["logout_time"].isoformat()
        
        return PaginatedResponse(
            success=True,
            message="成功獲取登入日誌",
            data=logs,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取登入日誌失敗: {str(e)}"
        )

@router.get("/dashboard", response_model=ApiResponse, summary="獲取儀表板統計")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user)
):
    """獲取儀表板統計資料"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 帳號統計
        cursor.execute("SELECT COUNT(*) as total_accounts FROM accounts")
        total_accounts = cursor.fetchone()["total_accounts"]
        
        cursor.execute("SELECT COUNT(*) as active_accounts FROM accounts WHERE status = 1")
        active_accounts = cursor.fetchone()["active_accounts"]
        
        cursor.execute("SELECT COUNT(*) as inactive_accounts FROM accounts WHERE status = 0")
        inactive_accounts = cursor.fetchone()["inactive_accounts"]
        
        cursor.execute("SELECT COUNT(*) as ptt_accounts FROM accounts WHERE account_type = 'PTT'")
        ptt_accounts = cursor.fetchone()["ptt_accounts"]
        
        cursor.execute("SELECT COUNT(*) as cmoney_accounts FROM accounts WHERE account_type = 'CMONEY'")
        cmoney_accounts = cursor.fetchone()["cmoney_accounts"]
        
        # 今日登入統計
        today = datetime.now().date()
        cursor.execute(
            "SELECT COUNT(*) as today_logins FROM login_logs WHERE DATE(login_time) = %s AND status = '成功'",
            (today,)
        )
        today_logins = cursor.fetchone()["today_logins"]
        
        cursor.execute(
            "SELECT COUNT(*) as today_failures FROM login_logs WHERE DATE(login_time) = %s AND status = '失敗'",
            (today,)
        )
        today_failures = cursor.fetchone()["today_failures"]
        
        cursor.close()
        conn.close()
        
        # 從任務追蹤中獲取進行中的任務數
        from api.routes.tasks import active_tasks
        from api.models import TaskStatus
        pending_tasks = len([task for task in active_tasks.values() if task["status"] == TaskStatus.PENDING])
        
        stats = DashboardStats(
            total_accounts=total_accounts,
            active_accounts=active_accounts,
            inactive_accounts=inactive_accounts,
            ptt_accounts=ptt_accounts,
            cmoney_accounts=cmoney_accounts,
            today_logins=today_logins,
            today_failures=today_failures,
            pending_tasks=pending_tasks
        )
        
        return ApiResponse(
            success=True,
            message="成功獲取儀表板統計",
            data=stats.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取儀表板統計失敗: {str(e)}"
        )

@router.get("/recent-activities", response_model=PaginatedResponse, summary="獲取最近活動")
async def get_recent_activities(
    limit: int = Query(20, le=100, description="查詢筆數限制"),
    current_user: dict = Depends(get_current_user)
):
    """獲取最近的登入活動"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查詢最近的登入活動
        cursor.execute("""
            SELECT 
                ll.id,
                ll.account_id,
                a.account as account_name,
                ll.site_name,
                ll.login_time,
                ll.logout_time,
                ll.status,
                ll.message
            FROM login_logs ll
            INNER JOIN accounts a ON ll.account_id = a.id
            ORDER BY ll.login_time DESC
            LIMIT %s
        """, (limit,))
        
        activities = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 轉換日期格式
        for activity in activities:
            if activity["login_time"]:
                activity["login_time"] = activity["login_time"].isoformat()
            if activity["logout_time"]:
                activity["logout_time"] = activity["logout_time"].isoformat()
        
        return PaginatedResponse(
            success=True,
            message="成功獲取最近活動",
            data=activities,
            total=len(activities),
            limit=limit,
            offset=0,
            has_next=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取最近活動失敗: {str(e)}"
        )

@router.get("/account/{account_id}/logs", response_model=PaginatedResponse, summary="獲取特定帳號的登入記錄")
async def get_account_logs(
    account_id: int,
    limit: int = Query(50, le=500, description="查詢筆數限制"),
    offset: int = Query(0, ge=0, description="查詢偏移量"),
    current_user: dict = Depends(get_current_user)
):
    """獲取特定帳號的登入記錄"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 檢查帳號是否存在
        cursor.execute("SELECT account FROM accounts WHERE id = %s", (account_id,))
        account = cursor.fetchone()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帳號不存在"
            )
        
        # 查詢總數
        cursor.execute(
            "SELECT COUNT(*) as total FROM login_logs WHERE account_id = %s",
            (account_id,)
        )
        total = cursor.fetchone()["total"]
        
        # 查詢登入記錄
        cursor.execute("""
            SELECT 
                id,
                account_id,
                site_name,
                login_time,
                logout_time,
                status,
                message
            FROM login_logs
            WHERE account_id = %s
            ORDER BY login_time DESC
            LIMIT %s OFFSET %s
        """, (account_id, limit, offset))
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 轉換日期格式
        for log in logs:
            if log["login_time"]:
                log["login_time"] = log["login_time"].isoformat()
            if log["logout_time"]:
                log["logout_time"] = log["logout_time"].isoformat()
            # 添加帳號名稱
            log["account_name"] = account["account"]
        
        return PaginatedResponse(
            success=True,
            message=f"成功獲取帳號 {account['account']} 的登入記錄",
            data=logs,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取帳號登入記錄失敗: {str(e)}"
        )
