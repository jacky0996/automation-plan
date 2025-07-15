import time
import sys
import random
import datetime
import os
import threading
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  # 導入資料庫設定

class LoginManager:
    """
    網站自動登入管理系統的核心類
    負責通用功能如資料庫連接、日誌記錄等
    """
    
    def __init__(self, site_name, account, password):
        self.site_name = site_name
        self.account = account
        self.password = password
        
        # MySQL 連接設定 - 從 config.py 讀取，同時添加池設定
        self.db_config = {
            'host': DB_CONFIG['host'],
            'user': DB_CONFIG['user'],
            'password': DB_CONFIG['password'],
            'database': DB_CONFIG['database'],
            'pool_name': f'mypool_{site_name}_{account}',
            'pool_size': 5
        }
        self.conn = None
        self._connect_db()
        self.account_id = self._get_account_id()
    
    def _connect_db(self):
        try:
            if not self.conn or not self.conn.is_connected():
                self.conn = mysql.connector.connect(**self.db_config)
        except Error as e:
            print(f"資料庫連接錯誤: {e}")
    
    def _get_account_id(self):
        try:
            cursor = self.conn.cursor()
            # 檢查帳號是否存在
            cursor.execute("SELECT id FROM accounts WHERE account = %s", (self.account,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                print(f"找不到帳號 {self.account} 的資料")
                return None
                
        except Error as e:
            print(f"資料庫操作錯誤: {e}")
            return None
    
    def log_login_attempt(self, status, message=""):
        try:
            self._connect_db()
            cursor = self.conn.cursor()
            
            # 獲取當前登入次數
            cursor.execute(
                "SELECT COUNT(*) FROM login_logs WHERE account_id = %s AND status = '失敗' AND login_time >= DATE_SUB(NOW(), INTERVAL 1 DAY)",
                (self.account_id,)
            )
            failed_count = cursor.fetchone()[0] + 1
            
            # 如果登入失敗次數超過3次，將帳號狀態改為0
            if status == "失敗" and failed_count >= 3:
                cursor.execute(
                    "UPDATE accounts SET status = 0 WHERE id = %s",
                    (self.account_id,)
                )
                message = f"{message} | 登入失敗超過3次，帳號已停用"
            
            # 如果登入成功，計算下次登入時間
            if status == "成功":
                next_login_time = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(
                    hour=random.randint(0, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                message = f"下次登入時間: {next_login_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 記錄登入日誌
            cursor.execute("""
                INSERT INTO login_logs 
                (account_id, login_time, status, message, login_count, site_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                self.account_id,
                datetime.datetime.now(),
                status,
                message,
                failed_count if status == "失敗" else 1,
                self.site_name
            ))
            self.conn.commit()
            print(f"網站: {self.site_name} | 帳號: {self.account} | 狀態: {status} | {message}")
            
        except Error as e:
            print(f"資料庫記錄錯誤: {e}")
            self._connect_db()
    
    def log_activity(self, action, status, message=""):
        try:
            self._connect_db()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_log 
                (account_id, action, status, message, site_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.account_id,
                action,
                status,
                message,
                self.site_name
            ))
            self.conn.commit()
            
        except Error as e:
            print(f"活動記錄錯誤: {e}")
            self._connect_db()
    
    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def _get_log_filename(self):
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        return f"{current_date}_{self.site_name}_{self.account}_logging.log"