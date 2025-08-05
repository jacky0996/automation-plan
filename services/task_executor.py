"""
任務執行器模組
處理後台任務的執行、監控和管理
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskExecutor:
    """任務執行器類"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(
        self, 
        task_type: str,
        task_data: Dict[str, Any],
        created_by: str = "system"
    ) -> str:
        """創建新任務"""
        task_id = str(uuid.uuid4())
        
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "status": TaskStatus.PENDING,
            "data": task_data,
            "created_by": created_by,
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error_message": None,
            "progress": 0
        }
        
        logger.info(f"任務已創建: {task_id} ({task_type})")
        return task_id
    
    async def execute_task(self, task_id: str):
        """執行任務"""
        if task_id not in self.tasks:
            logger.error(f"任務不存在: {task_id}")
            return
        
        task = self.tasks[task_id]
        
        try:
            # 更新任務狀態
            task["status"] = TaskStatus.RUNNING
            task["started_at"] = datetime.now()
            
            logger.info(f"開始執行任務: {task_id}")
            
            # 根據任務類型執行不同的邏輯
            if task["type"] == "login":
                result = await self._execute_login_task(task_id, task["data"])
            else:
                raise ValueError(f"未知的任務類型: {task['type']}")
            
            # 任務完成
            task["status"] = TaskStatus.COMPLETED
            task["completed_at"] = datetime.now()
            task["result"] = result
            task["progress"] = 100
            
            logger.info(f"任務執行完成: {task_id}")
            
        except Exception as e:
            # 任務失敗
            task["status"] = TaskStatus.FAILED
            task["completed_at"] = datetime.now()
            task["error_message"] = str(e)
            task["progress"] = 0
            
            logger.error(f"任務執行失敗: {task_id} - {e}")
        
        finally:
            # 清理運行中的任務記錄
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _execute_login_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行登入任務"""
        site_type = task_data.get("site_type")
        account_ids = task_data.get("account_ids", [])
        
        if not site_type or not account_ids:
            raise ValueError("缺少必要的任務參數")
        
        # 導入服務
        from services.login_service import LoginService
        login_service = LoginService()
        
        # 獲取帳號資訊
        accounts = login_service.get_accounts_by_ids(account_ids, site_type)
        if not accounts:
            raise ValueError("沒有找到符合條件的帳號")
        
        results = []
        total_accounts = len(accounts)
        
        for i, account in enumerate(accounts):
            try:
                # 更新進度
                progress = int((i / total_accounts) * 100)
                self.tasks[task_id]["progress"] = progress
                
                logger.info(f"處理帳號 {i+1}/{total_accounts}: {account['account']}")
                
                # 執行登入
                success = login_service.process_single_account(
                    account["account_type"],
                    account["account"],
                    account["password"]
                )
                
                results.append({
                    "account_id": account["id"],
                    "account": account["account"],
                    "success": success,
                    "processed_at": datetime.now().isoformat()
                })
                
                # 帳號之間的延遲
                if i < total_accounts - 1:
                    await asyncio.sleep(5)  # 等待 5 秒
                
            except Exception as e:
                logger.error(f"處理帳號 {account['account']} 時發生錯誤: {e}")
                results.append({
                    "account_id": account["id"],
                    "account": account["account"],
                    "success": False,
                    "error": str(e),
                    "processed_at": datetime.now().isoformat()
                })
        
        # 統計結果
        successful = len([r for r in results if r["success"]])
        failed = len([r for r in results if not r["success"]])
        
        return {
            "total_accounts": total_accounts,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_accounts) * 100 if total_accounts > 0 else 0,
            "details": results
        }
    
    def start_task(self, task_id: str) -> bool:
        """啟動任務執行"""
        if task_id not in self.tasks:
            logger.error(f"任務不存在: {task_id}")
            return False
        
        if task_id in self.running_tasks:
            logger.warning(f"任務已在執行中: {task_id}")
            return False
        
        # 創建異步任務
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.execute_task(task_id))
        self.running_tasks[task_id] = task
        
        return True
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 如果任務正在執行，嘗試取消
        if task_id in self.running_tasks:
            asyncio_task = self.running_tasks[task_id]
            asyncio_task.cancel()
            del self.running_tasks[task_id]
        
        # 更新任務狀態
        task["status"] = TaskStatus.CANCELLED
        task["completed_at"] = datetime.now()
        task["error_message"] = "任務被使用者取消"
        
        logger.info(f"任務已取消: {task_id}")
        return True
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務資訊"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """獲取所有任務"""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Dict[str, Any]]:
        """根據狀態獲取任務"""
        return [task for task in self.tasks.values() if task["status"] == status]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理舊任務"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task["completed_at"]:
                age = (current_time - task["completed_at"]).total_seconds() / 3600
                if age > max_age_hours:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.info(f"清理舊任務: {task_id}")
        
        return len(tasks_to_remove)

# 全域任務執行器實例
task_executor = TaskExecutor()
