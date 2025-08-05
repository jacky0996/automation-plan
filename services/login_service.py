"""
登入服務模組
重構原本的登入邏輯，使其可以被 API 調用
"""

import time
import datetime
import logging
import sys
import random
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class LoginService:
    """登入服務類，處理各種網站的登入邏輯"""
    
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        return mysql.connector.connect(**self.db_config)
    
    def get_accounts_due_for_login(self) -> List[Dict[str, Any]]:
        """從資料庫獲取需要登入的帳號（原本 main.py 的邏輯）"""
        accounts = []
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            current_time = datetime.datetime.now()
            logger.info(f"獲取需要登入的帳號，當前時間: {current_time}")
            
            # 簡化查詢邏輯 - 直接查詢符合條件的帳號
            query = """
                SELECT a.id, a.account, a.password, a.account_type as site_type 
                FROM accounts a 
                WHERE a.status = 1 
                AND a.account_type IN ('PTT', 'CMONEY')
            """
            
            cursor.execute(query)
            all_accounts = cursor.fetchall()
            
            for account in all_accounts:
                # 查詢該帳號的最新登入記錄
                login_query = """
                    SELECT ll.message, ll.login_time
                    FROM login_logs ll
                    WHERE ll.account_id = %s
                    AND ll.status = '成功'
                    AND ll.message LIKE '下次登入時間:%'
                    ORDER BY ll.login_time DESC
                    LIMIT 1
                """
                cursor.execute(login_query, (account['id'],))
                login_result = cursor.fetchone()
                
                if login_result:
                    try:
                        # 提取時間字符串
                        time_str = login_result['message'].replace('下次登入時間:', '').strip()
                        next_login_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                        
                        if next_login_time <= current_time:
                            logger.info(f"帳號 {account['account']} ({account['site_type']}) 需要登入 - 下次登入時間: {next_login_time}, 當前時間: {current_time}")
                            accounts.append({
                                'id': account['id'],
                                'account': account['account'], 
                                'password': account['password'],
                                'site_type': account['site_type']
                            })
                        else:
                            logger.info(f"帳號 {account['account']} ({account['site_type']}) 還不需要登入 - 下次登入時間: {next_login_time}")
                            
                    except Exception as time_error:
                        logger.error(f"解析帳號 {account['account']} 的登入時間時出錯: {time_error}")
                        logger.error(f"原始訊息: {login_result['message']}")
                else:
                    # 沒有登入記錄的帳號，視為需要登入
                    logger.info(f"帳號 {account['account']} ({account['site_type']}) 沒有登入記錄，需要登入")
                    accounts.append({
                        'id': account['id'],
                        'account': account['account'], 
                        'password': account['password'],
                        'site_type': account['site_type']
                    })
            
            cursor.close()
            conn.close()
            
            logger.info(f"找到 {len(accounts)} 個需要登入的帳號")
            return accounts
            
        except Exception as e:
            logger.error(f"獲取需要登入的帳號時發生錯誤: {e}")
            return []
    
    def process_single_account(self, site_type: str, account: str, password: str) -> bool:
        """處理單一帳號登入"""
        try:
            if site_type.lower() == 'ptt':
                # 動態導入 pttLogin 模組，避免循環導入問題
                from pttLogin import process_login as ptt_process
                logger.info(f"開始處理 PTT 帳號: {account}")
                return ptt_process(account, password)
                
            elif site_type.lower() == 'cmoney':
                # 動態導入 cmoneyLogin 模組
                from cmoneyLogin import process_login as cmoney_process
                logger.info(f"開始處理 CMONEY 帳號: {account}")
                return cmoney_process(account, password)
                
            else:
                logger.error(f"不支持的網站類型: {site_type}")
                return False
                    
        except Exception as e:
            logger.error(f"處理網站: {site_type} | 帳號: {account} 時發生錯誤: {e}")
            return False
    
    def process_multiple_accounts(self, accounts: List[Dict[str, Any]], delay_range: tuple = (5, 15)) -> Dict[str, Any]:
        """處理多個帳號登入"""
        results = {
            "total": len(accounts),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for i, account_info in enumerate(accounts):
            try:
                logger.info(f"處理帳號 {i+1}/{len(accounts)}: {account_info['account']}")
                
                # 處理單個帳號
                success = self.process_single_account(
                    account_info['site_type'],
                    account_info['account'],
                    account_info['password']
                )
                
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "account": account_info['account'],
                    "site_type": account_info['site_type'],
                    "success": success
                })
                
                # 每個帳號之間隨機等待
                if i < len(accounts) - 1:  # 如果不是最後一個帳號
                    wait_time = random.randint(delay_range[0], delay_range[1])
                    logger.info(f"等待 {wait_time} 秒處理下一個帳號...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"處理帳號 {account_info['account']} 時發生錯誤: {e}")
                results["failed"] += 1
                results["details"].append({
                    "account": account_info['account'],
                    "site_type": account_info['site_type'],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def get_account_info(self, account_id: int) -> Optional[Dict[str, Any]]:
        """獲取特定帳號資訊"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT id, account, password, account_type, status FROM accounts WHERE id = %s",
                (account_id,)
            )
            account = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return account
            
        except Exception as e:
            logger.error(f"獲取帳號資訊失敗: {e}")
            return None
    
    def get_accounts_by_ids(self, account_ids: List[int], site_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """根據 ID 列表獲取帳號資訊"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 建立查詢條件
            placeholders = ','.join(['%s'] * len(account_ids))
            query = f"SELECT id, account, password, account_type FROM accounts WHERE id IN ({placeholders}) AND status = 1"
            params = account_ids
            
            if site_type:
                query += " AND account_type = %s"
                params.append(site_type)
            
            cursor.execute(query, params)
            accounts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return accounts
            
        except Exception as e:
            logger.error(f"獲取帳號列表失敗: {e}")
            return []
    
    def check_account_login_status(self, account_id: int) -> Dict[str, Any]:
        """檢查帳號登入狀態"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 獲取最新登入記錄
            cursor.execute("""
                SELECT login_time, status, message
                FROM login_logs
                WHERE account_id = %s
                ORDER BY login_time DESC
                LIMIT 1
            """, (account_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return {
                    "needs_login": True,
                    "reason": "沒有登入記錄"
                }
            
            if result["status"] != "成功":
                return {
                    "needs_login": True,
                    "reason": "上次登入失敗"
                }
            
            # 檢查下次登入時間
            if "下次登入時間:" in result["message"]:
                try:
                    time_str = result["message"].replace("下次登入時間:", "").strip()
                    next_login_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    current_time = datetime.datetime.now()
                    
                    if next_login_time <= current_time:
                        return {
                            "needs_login": True,
                            "reason": f"已到下次登入時間: {next_login_time}"
                        }
                    else:
                        return {
                            "needs_login": False,
                            "next_login_time": next_login_time.isoformat(),
                            "reason": f"下次登入時間: {next_login_time}"
                        }
                except Exception as e:
                    logger.error(f"解析登入時間失敗: {e}")
                    return {
                        "needs_login": True,
                        "reason": "無法解析下次登入時間"
                    }
            
            return {
                "needs_login": True,
                "reason": "無法確定下次登入時間"
            }
            
        except Exception as e:
            logger.error(f"檢查登入狀態失敗: {e}")
            return {
                "needs_login": True,
                "reason": f"檢查失敗: {str(e)}"
            }
