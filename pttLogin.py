import time
import sys
import random
import datetime
import os
import threading
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG  # 導入資料庫設定

# 導入各個功能模組
from pttLoginModule import PttLoginBot
from pttPushModule import PttPushBot
from pttPostModule import PttPostBot

class PttBot(PttLoginBot, PttPushBot, PttPostBot):
    """整合所有 PTT 功能的主類"""
    
    def __init__(self, account, password):
        super().__init__(account, password)
    
    def login_and_perform_tasks(self):
        """登入並執行所有任務"""
        try:
            if self.login():
                print(f"帳號 {self.account} 登入成功，開始執行任務...")
                
                # 檢查推文任務
                print("檢查和創建推文任務...")
                self.check_and_create_push_tasks()
                
                # 執行推文任務
                print("執行推文任務...")
                push_count = self.execute_push_tasks()
                print(f"完成 {push_count} 個推文任務")
                
                # 執行發文任務
                print("執行發文任務...")
                post_count = self.execute_pending_posts()
                print(f"完成 {post_count} 個發文任務")
                
                # 登出
                print(f"所有任務完成，準備登出...")
                time.sleep(random.randint(3, 8))  # 隨機等待一段時間再登出
                self.logout()
                return True
            else:
                print(f"帳號 {self.account} 登入失敗，無法執行任務")
                return False
        except Exception as e:
            print(f"執行任務時發生錯誤: {e}")
            return False

def process_login(account, password):
    """處理 PTT 登入功能，提供給 main.py 調用"""
    bot = PttBot(account, password)
    
    try:
        # 檢查是否應該登入
        if hasattr(bot, 'should_login_now') and callable(bot.should_login_now):
            if not bot.should_login_now():
                print(f"帳號 {account} 目前不需要登入")
                return False
                
        # 使用整合類的登入與任務執行方法
        return bot.login_and_perform_tasks()
        
    except Exception as e:
        print(f"處理帳號 {account} 時發生錯誤: {e}")
        # 確保登出
        try:
            if bot.ptt_bot.is_login:
                bot.logout()
        except:
            pass
        return False

if __name__ == "__main__":
    try:
        # 從資料庫讀取帳號，使用 config.py 中的設定
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT account, password FROM accounts")
        accounts = cursor.fetchall()
        conn.close()
        
        print(f"總共讀取到 {len(accounts)} 組帳號")
        
        # 建立執行緒列表
        threads = []
        
        # 將函數定義在循環外部
        def run_tasks(acc, pwd):
            bot = PttBot(acc, pwd)
            return bot.login_and_perform_tasks()
        
        # 為每個帳號建立一個執行緒
        for index, (account, password) in enumerate(accounts, 1):
            print(f"\n開始處理第 {index} 組帳號: {account}")
            
            thread = threading.Thread(
                target=run_tasks,
                args=(account, password)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有執行緒完成
        for thread in threads:
            thread.join()
            
        print("\n所有帳號處理完成")
                
    except Exception as e:
        print(f"發生錯誤: {e}")