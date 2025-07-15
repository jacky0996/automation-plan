import time
import datetime
import logging
import sys
import random
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

# 設置日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def process_account(site_type, account, password):
    """根據網站類型調用對應的登入模組處理帳號"""
    
    try:
        if site_type.lower() == 'ptt':
            # 動態導入 pttLogin 模組，避免循環導入問題
            from pttLogin import process_login as ptt_process
            logger.info(f"開始處理 PTT 帳號: {account}")
            ptt_process(account, password)
            
        elif site_type.lower() == 'cmoney':
            # 動態導入 cmoneyLogin 模組
            from cmoneyLogin import process_login as cmoney_process
            logger.info(f"開始處理 CMONEY 帳號: {account}")
            cmoney_process(account, password)
            
        # 可以擴展更多網站類型
        # elif site_type.lower() == 'othersite':
        #     from othersiteLogin import process_login as othersite_process
        #     othersite_process(account, password)
            
        else:
            logger.error(f"不支持的網站類型: {site_type}")
                
    except Exception as e:
        logger.error(f"處理網站: {site_type} | 帳號: {account} 時發生錯誤: {e}")

def get_accounts_due_for_login():
    """從資料庫獲取需要登入的帳號"""
    accounts = []
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        current_time = datetime.datetime.now()
        logger.info(f"獲取需要登入的帳號，當前時間: {current_time}")
        
        # 查詢符合登入條件的帳號:
        # 1. 帳號狀態為啟用(status=1)
        # 2. 最近一次登入記錄中的下次登入時間早於當前時間
        query = """
            SELECT a.id, a.account, a.password, a.account_type as site_type 
            FROM accounts a 
            WHERE a.status = 1 
            AND a.account_type IN ('CMONEY','PTT')
            AND EXISTS (
                SELECT 1 
                FROM login_logs ll
                WHERE ll.account_id = a.id
                AND ll.message LIKE '下次登入時間:%'
                AND STR_TO_DATE(
                    SUBSTRING_INDEX(SUBSTRING_INDEX(ll.message, ': ', -1), ' ', 1),
                    '%Y-%m-%d'
                ) <= CURDATE()
                ORDER BY ll.login_time DESC
                LIMIT 1
            )
        """
        
        cursor.execute(query)
        accounts = cursor.fetchall()
        
        if accounts:
            logger.info(f"找到 {len(accounts)} 個需要登入的帳號")
            for acc in accounts:
                logger.info(f"準備登入: {acc['site_type']} - {acc['account']}")
        else:
            logger.info("沒有找到需要登入的帳號")
            
        cursor.close()
        conn.close()
        
    except Error as e:
        logger.error(f"獲取帳號時發生錯誤: {e}")
    
    return accounts

def main():
    """主程序入口"""
    logger.info("=" * 50)
    logger.info("啟動自動登入檢查...")
    
    # 添加程序鎖，避免重複執行
    import os
    lock_file = '/tmp/login_process_lock'
    try:
        # 嘗試創建鎖文件
        if os.path.exists(lock_file):
            # 檢查鎖文件的創建時間
            mtime = os.path.getmtime(lock_file)
            file_time = datetime.datetime.fromtimestamp(mtime)
            now = datetime.datetime.now()
            
            # 如果鎖文件超過2小時，視為過期鎖
            if (now - file_time).total_seconds() > 7200:  # 2小時
                os.remove(lock_file)
            else:
                logger.warning("另一個登入程序正在運行，本次執行被跳過")
                return
        
        # 創建新的鎖文件
        with open(lock_file, 'w') as f:
            f.write(str(datetime.datetime.now()))
    except Exception as e:
        logger.error(f"處理程序鎖時出錯: {e}")
    
    try:
        # 添加一個隨機延遲 (1-5 分鐘)，避免每小時整點同時執行
        delay_seconds = random.randint(1, 5)
        logger.info(f"添加隨機延遲 {delay_seconds} 秒")
        time.sleep(delay_seconds)
        
        # 獲取需要登入的帳號
        accounts = get_accounts_due_for_login()
        
        if not accounts:
            logger.info("本次執行沒有需要登入的帳號，程式結束")
            # 清理鎖文件
            try:
                os.remove(lock_file)
            except:
                pass
            return
        
        # 逐個處理需要登入的帳號
        for account_info in accounts:
            try:
                # 處理單個帳號
                process_account(
                    account_info['site_type'],
                    account_info['account'],
                    account_info['password']
                )
                
                # 每個帳號之間隨機等待 5-15 秒
                if accounts.index(account_info) < len(accounts) - 1:  # 如果不是最後一個帳號
                    wait_time = random.randint(5, 15)
                    logger.info(f"等待 {wait_time} 秒處理下一個帳號...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"處理帳號 {account_info['account']} 時發生錯誤: {e}")
        
        logger.info("本次登入檢查完成，程式結束")
        
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")
    
    finally:
        # 清理鎖文件
        try:
            os.remove(lock_file)
        except:
            pass

if __name__ == "__main__":
    main()