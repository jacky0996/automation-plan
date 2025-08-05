"""
任務管理相關 API 路由
處理登入任務的建立、執行、監控
"""

import uuid
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from api.models import (
    TaskCreate, TaskResponse, ApiResponse, 
    PaginatedResponse, TaskStatus, SiteType
)
from api.auth import get_current_user
from services.task_executor import task_executor, TaskStatus as ExecTaskStatus
import mysql.connector
from config import DB_CONFIG

router = APIRouter()

def get_db_connection():
    """獲取資料庫連接"""
    return mysql.connector.connect(**DB_CONFIG)

@router.post("/", response_model=ApiResponse, summary="建立登入任務")
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """建立新的登入任務"""
    try:
        # 驗證帳號是否存在
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            f"SELECT COUNT(*) as count FROM accounts WHERE id IN ({','.join(['%s'] * len(task_data.account_ids))}) AND account_type = %s AND status = 1",
            task_data.account_ids + [task_data.site_type.value]
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result[0] == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="沒有找到符合條件的有效帳號"
            )
        
        # 使用新的任務執行器
        task_id = task_executor.create_task(
            task_type="login",
            task_data={
                "site_type": task_data.site_type.value,
                "account_ids": task_data.account_ids
            },
            created_by=current_user["username"]
        )
        
        # 啟動任務
        success = task_executor.start_task(task_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="啟動任務失敗"
            )
        
        return ApiResponse(
            success=True,
            message="任務建立並啟動成功",
            data={
                "task_id": task_id,
                "status": ExecTaskStatus.RUNNING,
                "account_count": len(task_data.account_ids)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立任務失敗: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse, summary="獲取任務列表")
async def get_tasks(
    limit: int = Query(50, le=500, description="查詢筆數限制"),
    offset: int = Query(0, ge=0, description="查詢偏移量"),
    status_filter: Optional[str] = Query(None, description="狀態篩選"),
    current_user: dict = Depends(get_current_user)
):
    """獲取任務列表"""
    try:
        # 從任務執行器獲取所有任務
        all_tasks = task_executor.get_all_tasks()
        
        # 狀態篩選
        if status_filter:
            all_tasks = [task for task in all_tasks if task["status"] == status_filter]
        
        # 排序（最新的在前面）
        all_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 分頁
        total = len(all_tasks)
        tasks = all_tasks[offset:offset + limit]
        
        # 轉換日期格式並清理敏感資訊
        for task in tasks:
            task["created_at"] = task["created_at"].isoformat()
            if task["started_at"]:
                task["started_at"] = task["started_at"].isoformat()
            if task["completed_at"]:
                task["completed_at"] = task["completed_at"].isoformat()
            
            # 移除敏感的帳號密碼資訊
            if "data" in task and "account_ids" in task["data"]:
                task["account_count"] = len(task["data"]["account_ids"])
            
        return PaginatedResponse(
            success=True,
            message="成功獲取任務列表",
            data=tasks,
            total=total,
            limit=limit,
            offset=offset,
            has_next=offset + limit < total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取任務列表失敗: {str(e)}"
        )

@router.get("/{task_id}", response_model=ApiResponse, summary="獲取任務詳情")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """根據 ID 獲取任務詳情"""
    try:
        task = task_executor.get_task(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任務不存在"
            )
        
        # 製作副本並轉換日期格式
        task_copy = task.copy()
        task_copy["created_at"] = task_copy["created_at"].isoformat()
        if task_copy["started_at"]:
            task_copy["started_at"] = task_copy["started_at"].isoformat()
        if task_copy["completed_at"]:
            task_copy["completed_at"] = task_copy["completed_at"].isoformat()
        
        return ApiResponse(
            success=True,
            message="成功獲取任務詳情",
            data=task_copy
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取任務詳情失敗: {str(e)}"
        )

@router.delete("/{task_id}", response_model=ApiResponse, summary="取消任務")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """取消執行中的任務"""
    try:
        task = task_executor.get_task(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任務不存在"
            )
        
        if task["status"] in [ExecTaskStatus.COMPLETED, ExecTaskStatus.FAILED, ExecTaskStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無法取消已完成的任務"
            )
        
        # 取消任務
        success = task_executor.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="取消任務失敗"
            )
        
        return ApiResponse(
            success=True,
            message="任務已取消",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任務失敗: {str(e)}"
        )

@router.post("/execute-all", response_model=ApiResponse, summary="執行所有待登入帳號")
async def execute_all_due_accounts(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """執行所有需要登入的帳號（類似原本的 main.py 功能）"""
    try:
        # 使用服務層獲取需要登入的帳號
        from services.login_service import LoginService
        login_service = LoginService()
        accounts = login_service.get_accounts_due_for_login()
        
        if not accounts:
            return ApiResponse(
                success=True,
                message="目前沒有需要登入的帳號",
                data={"account_count": 0}
            )
        
        # 按網站類型分組
        ptt_accounts = [acc for acc in accounts if acc["site_type"].upper() == "PTT"]
        cmoney_accounts = [acc for acc in accounts if acc["site_type"].upper() == "CMONEY"]
        
        task_ids = []
        
        # 為 PTT 帳號建立任務
        if ptt_accounts:
            account_ids = [acc["id"] for acc in ptt_accounts]
            task_id = task_executor.create_task(
                task_type="login",
                task_data={
                    "site_type": "PTT",
                    "account_ids": account_ids
                },
                created_by=current_user["username"]
            )
            
            task_executor.start_task(task_id)
            task_ids.append(task_id)
        
        # 為 CMoney 帳號建立任務
        if cmoney_accounts:
            account_ids = [acc["id"] for acc in cmoney_accounts]
            task_id = task_executor.create_task(
                task_type="login",
                task_data={
                    "site_type": "CMONEY",
                    "account_ids": account_ids
                },
                created_by=current_user["username"]
            )
            
            task_executor.start_task(task_id)
            task_ids.append(task_id)
        
        return ApiResponse(
            success=True,
            message=f"已建立並啟動 {len(task_ids)} 個任務，總共 {len(accounts)} 個帳號",
            data={
                "task_ids": task_ids,
                "total_accounts": len(accounts),
                "ptt_accounts": len(ptt_accounts),
                "cmoney_accounts": len(cmoney_accounts)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行任務失敗: {str(e)}"
        )

@router.get("/status/summary", response_model=ApiResponse, summary="獲取任務狀態摘要")
async def get_task_summary(
    current_user: dict = Depends(get_current_user)
):
    """獲取任務狀態摘要統計"""
    try:
        all_tasks = task_executor.get_all_tasks()
        
        summary = {
            "total": len(all_tasks),
            "pending": len([t for t in all_tasks if t["status"] == ExecTaskStatus.PENDING]),
            "running": len([t for t in all_tasks if t["status"] == ExecTaskStatus.RUNNING]),
            "completed": len([t for t in all_tasks if t["status"] == ExecTaskStatus.COMPLETED]),
            "failed": len([t for t in all_tasks if t["status"] == ExecTaskStatus.FAILED]),
            "cancelled": len([t for t in all_tasks if t["status"] == ExecTaskStatus.CANCELLED])
        }
        
        return ApiResponse(
            success=True,
            message="成功獲取任務狀態摘要",
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取任務摘要失敗: {str(e)}"
        )

@router.post("/cleanup", response_model=ApiResponse, summary="清理舊任務")
async def cleanup_old_tasks(
    max_age_hours: int = Query(24, description="任務最大保留時間（小時）"),
    current_user: dict = Depends(get_current_user)
):
    """清理指定時間之前的已完成任務"""
    try:
        cleaned_count = task_executor.cleanup_old_tasks(max_age_hours)
        
        return ApiResponse(
            success=True,
            message=f"已清理 {cleaned_count} 個舊任務",
            data={"cleaned_count": cleaned_count, "max_age_hours": max_age_hours}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理任務失敗: {str(e)}"
        )
