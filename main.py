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

def _log_login_attempt(status, message=None):
    """記錄登入嘗試"""
    try:
        if not self.conn or not self.account_id:
            print("無法記錄登入嘗試: 資料庫未連接或帳號ID未知")
            return
            
        cursor = self.conn.cursor()
        
        # 如果登入成功，計算下次登入時間
        if status == "成功":
            # 計算下次登入時間（隔天的隨機時間）
            next_login_time = self._calculate_next_login_time()
            login_message = f"{message}，下次登入時間: {next_login_time}"
            print(f"下次登入時間: {next_login_time}")
        else:
            login_message = message
        
        # 記錄登入日誌
        cursor.execute("""
            INSERT INTO login_logs (account_id, site_name, login_time, status, message)
            VALUES (%s, %s, NOW(), %s, %s)
        """, (self.account_id, 'CMONEY', status, login_message))
        
        # 獲取剛插入的日誌ID
        self.log_id = cursor.lastrowid
        
        self.conn.commit()
        cursor.close()

        print(f"已記錄登入嘗試：{status}")
        
    except Exception as e:
        print(f"記錄登入嘗試時出錯: {e}")

def _calculate_next_login_time():
    """計算下次登入時間 - 隔天的隨機時間"""
    import random
    from datetime import datetime, timedelta
    
    try:
        # 取得明天的日期
        tomorrow = datetime.now() + timedelta(days=1)
        
        # 隨機選擇時間範圍（例如：早上8點到晚上10點）
        start_hour = 8   # 早上8點
        end_hour = 22    # 晚上10點
        
        # 隨機選擇小時和分鐘
        random_hour = random.randint(start_hour, end_hour)
        random_minute = random.randint(0, 59)
        random_second = random.randint(0, 59)
        
        # 組合成完整的下次登入時間
        next_login_time = tomorrow.replace(
            hour=random_hour,
            minute=random_minute,
            second=random_second,
            microsecond=0
        )
        
        return next_login_time.strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        print(f"計算下次登入時間時發生錯誤: {e}")
        # 如果出錯，預設為明天中午12點
        tomorrow_noon = (datetime.now() + timedelta(days=1)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        return tomorrow_noon.strftime("%Y-%m-%d %H:%M:%S")

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