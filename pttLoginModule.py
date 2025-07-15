import datetime
import time
import threading
import random
from pttBase import PttBaseBot

class PttLoginBot(PttBaseBot):
    """處理 PTT 登入和登出功能的機器人類"""
    
    def login(self):
        """執行 PTT 登入"""
        try:
            print(f"開始 PTT 登入流程，帳號：{self.account}")
            self.ptt_bot.login(
                self.account,
                self.password
            )
            print("PTT 登入成功")
            
            # 記錄登入成功
            self.log_login_attempt("成功")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"PTT 登入失敗：{error_msg}")
            self.log_login_attempt("失敗", f"登入失敗：{error_msg}")
            return False

    def logout(self):
        """執行 PTT 登出"""
        try:
            self.ptt_bot.logout()
            
            # 更新最後一筆登入記錄的登出時間
            self._connect_db()
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE login_logs 
                SET logout_time = %s
                WHERE account_id = %s 
                AND site_name = 'PTT'
                AND logout_time IS NULL
                ORDER BY login_time DESC 
                LIMIT 1
            """, (datetime.datetime.now(), self.account_id))
            self.conn.commit()
            
            print("登出成功")
        except Exception as e:
            print(f"登出失敗: {e}")

    def should_login_now(self):
        """檢查當前是否應該登入"""
        try:
            self._connect_db()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT message 
                FROM login_logs 
                WHERE account_id = %s AND status = '成功'
                ORDER BY login_time DESC 
                LIMIT 1
            """, (self.account_id,))
            result = cursor.fetchone()
            
            # 如果沒有登入記錄，應該立即登入
            if not result:
                return True
                
            # 檢查是否有下次登入時間的信息
            if result and "下次登入時間:" in result[0]:
                try:
                    next_login_time = datetime.datetime.strptime(
                        result[0].split(": ")[1],
                        "%Y-%m-%d %H:%M:%S"
                    )
                    
                    # 如果當前時間已經超過下次登入時間，則應該登入
                    now = datetime.datetime.now()
                    return now >= next_login_time
                except Exception as e:
                    print(f"解析下次登入時間時出錯: {e}")
                    return True
            
            # 如果沒有找到下次登入時間信息，預設為應該登入
            return True
            
        except Exception as e:
            print(f"檢查是否應該登入時出錯: {e}")
            return False