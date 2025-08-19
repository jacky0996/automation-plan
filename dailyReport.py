import mysql.connector
import requests
import json
import os
from datetime import datetime
from collections import defaultdict
from config import DB_CONFIG

LINE_TOKEN = os.getenv('line_token')

class DailyReportGenerator:
    """每日登入報告生成器"""
    
    def __init__(self):
        self.conn = None
    
    def _connect_db(self):
        """連接資料庫"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"資料庫連接失敗: {e}")
            return False
    
    def _close_db(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def get_active_accounts(self):
        """取得所有啟用的帳號，依 account_type 分組"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            query = """
                SELECT account_type, COUNT(*) as total_count
                FROM accounts 
                WHERE status = 1
                GROUP BY account_type
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # 轉換為字典格式
            active_accounts = {}
            for result in results:
                account_type = result['account_type'].upper()
                active_accounts[account_type] = result['total_count']
            
            return active_accounts
            
        except Exception as e:
            print(f"取得啟用帳號統計時發生錯誤: {e}")
            return {}
    
    def get_today_login_accounts(self):
        """取得今日成功登入的帳號，依 account_type 分組"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            query = """
                SELECT a.account_type, COUNT(DISTINCT ll.account_id) as login_count
                FROM login_logs ll
                JOIN accounts a ON ll.account_id = a.id
                WHERE DATE(ll.login_time) = CURDATE()
                AND ll.status = '成功'
                AND a.status = 1
                GROUP BY a.account_type
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # 轉換為字典格式
            login_accounts = {}
            for result in results:
                account_type = result['account_type'].upper()
                login_accounts[account_type] = result['login_count']
            
            return login_accounts
            
        except Exception as e:
            print(f"取得今日登入帳號統計時發生錯誤: {e}")
            return {}
    
    def get_today_login_details(self):
        """取得今日成功登入的帳號詳細資訊"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            query = """
                SELECT DISTINCT 
                    a.account, 
                    a.account_type,
                    ll.login_time
                FROM login_logs ll
                JOIN accounts a ON ll.account_id = a.id
                WHERE DATE(ll.login_time) = CURDATE()
                AND ll.status = '成功'
                AND a.status = 1
                ORDER BY a.account_type, ll.login_time
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Exception as e:
            print(f"取得今日登入帳號詳細資訊時發生錯誤: {e}")
            return []
    
    def generate_summary_report(self):
        """生成摘要報告"""
        try:
            if not self._connect_db():
                return "無法連接資料庫"
            
            # 取得統計資料
            active_accounts = self.get_active_accounts()
            login_accounts = self.get_today_login_accounts()
            
            # 生成報告字串
            today = datetime.now().strftime("%Y-%m-%d")
            report_lines = [f"=== 每日登入報告 ({today}) ==="]
            
            # 處理每種帳號類型
            all_types = set(active_accounts.keys()) | set(login_accounts.keys())
            
            for account_type in sorted(all_types):
                total_count = active_accounts.get(account_type, 0)
                login_count = login_accounts.get(account_type, 0)
                
                type_name = account_type.lower()
                report_lines.append(
                    f"{type_name}自動計畫共有{total_count}個帳號執行，今天登入{login_count}個帳號"
                )
            
            # 計算總計
            total_active = sum(active_accounts.values())
            total_login = sum(login_accounts.values())
            report_lines.append(f"總計：共有{total_active}個帳號執行，今天登入{total_login}個帳號")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"生成摘要報告時發生錯誤: {e}"
        finally:
            self._close_db()
    
    def generate_detailed_report(self):
        """生成詳細報告"""
        try:
            if not self._connect_db():
                return "無法連接資料庫"
            
            # 取得統計資料和詳細資訊
            active_accounts = self.get_active_accounts()
            login_accounts = self.get_today_login_accounts()
            login_details = self.get_today_login_details()
            
            # 生成報告字串
            today = datetime.now().strftime("%Y-%m-%d")
            report_lines = [f"=== 每日登入詳細報告 ({today}) ===\n"]
            
            # 摘要部分
            report_lines.append("【摘要統計】")
            all_types = set(active_accounts.keys()) | set(login_accounts.keys())
            
            for account_type in sorted(all_types):
                total_count = active_accounts.get(account_type, 0)
                login_count = login_accounts.get(account_type, 0)
                
                type_name = account_type.lower()
                report_lines.append(
                    f"{type_name}自動計畫共有{total_count}個帳號執行，今天登入{login_count}個帳號"
                )
            
            # 計算總計
            total_active = sum(active_accounts.values())
            total_login = sum(login_accounts.values())
            report_lines.append(f"總計：共有{total_active}個帳號執行，今天登入{total_login}個帳號\n")
            
            # 詳細登入記錄
            if login_details:
                report_lines.append("【今日登入詳細記錄】")
                
                # 按帳號類型分組
                grouped_details = defaultdict(list)
                for detail in login_details:
                    grouped_details[detail['account_type']].append(detail)
                
                for account_type in sorted(grouped_details.keys()):
                    type_name = account_type.upper()
                    report_lines.append(f"\n{type_name} 帳號:")
                    
                    for detail in grouped_details[account_type]:
                        login_time = detail['login_time'].strftime("%H:%M:%S")
                        report_lines.append(f"  - {detail['account']} (登入時間: {login_time})")
            else:
                report_lines.append("【今日登入詳細記錄】")
                report_lines.append("今日無帳號成功登入")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"生成詳細報告時發生錯誤: {e}"
        finally:
            self._close_db()

    def daily_report(self, report_content):
        """發送每日報告到 LINE"""
        try:
            if not LINE_TOKEN:
                print("LINE_TOKEN 未設定，跳過 LINE 通知")
                return False
            
            print(f"準備發送報告到 LINE...")
            
            # LINE Bot API 設定
            headers = {
                'Authorization': f'Bearer {LINE_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            url = 'https://api.line.me/v2/bot/message/broadcast'
            body = {
                'messages': [{
                    'type': 'text',
                    'text': report_content
                }]
            }
            
            req = requests.post(url, headers=headers, data=json.dumps(body).encode('utf-8'))
            
            if req.status_code == 200:
                print("LINE 報告發送成功")
                print(f"回應: {req.text}")
                return True
            else:
                print(f"LINE 報告發送失敗，狀態碼: {req.status_code}")
                print(f"錯誤訊息: {req.text}")
                return False
                
        except Exception as e:
            print(f"發送 LINE 報告時發生錯誤: {e}")
            return False
        

def main():
    """主程式入口"""
    try:
        generator = DailyReportGenerator()
        
        # 生成摘要報告
        print("生成每日登入摘要報告...")
        summary_report = generator.generate_summary_report()
        print(summary_report)
        print()
        
        # 生成詳細報告
        print("生成每日登入詳細報告...")
        detailed_report = generator.generate_detailed_report()
        print(detailed_report)

        generator.daily_report(detailed_report)

    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"\n程式執行錯誤: {e}")

if __name__ == "__main__":
    main()