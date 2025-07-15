import PyPtt
import time
import random
import datetime
import mysql.connector
from mysql.connector import Error
from loginManager import LoginManager
from config import DB_CONFIG

class PttBaseBot(LoginManager):
    """PTT 基礎機器人類，提供共用功能"""
    
    def __init__(self, account, password):
        super().__init__('PTT', account, password)  # 呼叫父類初始化，指定網站名稱為 'PTT'
        self.ptt_bot = PyPtt.API()
        
    def _connect_db(self):
        """建立與資料庫的連接"""
        try:
            if not self.conn or not self.conn.is_connected():
                self.conn = mysql.connector.connect(**self.db_config)
        except Error as e:
            print(f"資料庫連接錯誤: {e}")

    def _get_account_id(self):
        """獲取當前帳號的 ID"""
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