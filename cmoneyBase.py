import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from datetime import datetime
import os

class CMoneyBase:
    """CMONEY 機器人的基礎類別，處理帳號事務和資料庫操作"""
    
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.conn = self._connect_db()
        self.account_id = self._get_account_id()
        
    def _connect_db(self):
        """連接到資料庫並設定時區"""
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SET time_zone = '+08:00'")
            conn.commit()
            cursor.close()
            return conn
        except Exception as e:
            print(f"資料庫連接錯誤: {e}")
            return None
            
    def _get_account_id(self):
        """從資料庫獲取帳號 ID"""
        try:
            if not self.conn:
                print("無法獲取帳號ID: 資料庫未連接")
                return None
                
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM accounts WHERE account = %s AND account_type = 'CMONEY'", (self.account,))
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return result['id']
            else:
                print(f"找不到 CMONEY 帳號: {self.account}")
                return None
        except Exception as e:
            print(f"獲取帳號ID時出錯: {e}")
            return None
    
    def _remove_lock_file(self):
        """移除登入鎖定檔案"""
        try:
            lock_file = f"{self.account}.lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception as e:
            print(f"移除鎖定檔案時發生錯誤：{str(e)}")
    
    def log_activity(self, activity_type, success, message):
        """記錄活動到資料庫"""
        try:
            if not self.conn or not self.account_id:
                print("無法記錄活動: 資料庫未連接或帳號ID未知")
                return
                
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (account_id, action, action_time, status, message, site_name)
                VALUES (%s, %s, NOW(), %s, %s, %s)
            """, (self.account_id, activity_type, 1 if success else 0, message, 'CMONEY'))
            
            self.conn.commit()
            cursor.close()
            print(f"已記錄活動: {activity_type} - {message}")
            
        except Exception as e:
            print(f"記錄活動時出錯: {e}")
    
    def should_login_now(self):
        """檢查是否應該登入"""
        try:
            if not self.conn or not self.account_id:
                print("無法檢查是否應該登入: 資料庫未連接或帳號ID未知")
                return True
                
            cursor = self.conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT message, login_time
                FROM login_logs
                WHERE account_id = %s AND site_name = 'CMONEY'
                ORDER BY login_time DESC
                LIMIT 1
            """, (self.account_id,))
            
            log_result = cursor.fetchone()
            cursor.close()
            
            if not log_result:
                print("沒有找到登入記錄，應該進行登入")
                return True
            
            if log_result['message'] and '下次登入時間:' in log_result['message']:
                next_login_date_str = log_result['message'].split('下次登入時間:')[1].strip().split(' ')[0]
                next_login_date = datetime.strptime(next_login_date_str, '%Y-%m-%d').date()
                today = datetime.now().date()
                
                print(f"下次登入時間: {next_login_date}, 今天: {today}")
                return today >= next_login_date
            
            return True
            
        except Exception as e:
            print(f"檢查是否應該登入時出錯: {e}")
            return True
    
    def get_pending_posts(self):
        """從資料庫獲取待發布的文章"""
        try:
            if not self.conn or not self.account_id:
                print("無法獲取待發布文章: 資料庫未連接或帳號ID未知")
                return []
                
            cursor = self.conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, board, title, content, scheduled_time
                FROM posts
                WHERE account_id = %s 
                  AND site_name = 'CMONEY'
                  AND (result IS NULL OR result != 'success')
                  AND scheduled_time <= NOW()
                ORDER BY scheduled_time ASC
            """, (self.account_id,))
            
            posts = cursor.fetchall()
            cursor.close()
            
            return posts
            
        except Exception as e:
            print(f"獲取待發布文章時出錯: {e}")
            return []
    
    def update_post_status(self, post_id, result, article_id=None, article_url=None, result_message=None):
        """更新文章發布狀態"""
        try:
            if not self.conn:
                print("無法更新文章狀態: 資料庫未連接")
                return False
                
            cursor = self.conn.cursor()
            
            if result == 'success':
                cursor.execute("""
                    UPDATE posts 
                    SET result = 'success', 
                        article_id = %s,
                        article_url = %s,
                        post_time = NOW()
                    WHERE id = %s
                """, (article_id, article_url, post_id))
            else:
                cursor.execute("""
                    UPDATE posts 
                    SET result = 'fail',
                        result_message = %s,
                        post_time = NOW()
                    WHERE id = %s
                """, (result_message, post_id))
                
            self.conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"更新文章狀態時出錯: {e}")
            return False
            
    def __del__(self):
        """確保完全釋放所有資源"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception as e:
            print(f"釋放資料庫資源時發生錯誤: {e}")