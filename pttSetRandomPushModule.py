import mysql.connector
from mysql.connector import Error
import random
import datetime
import time
import PyPtt
from pttBase import PttBaseBot

class PttSetRandomPushBot(PttBaseBot):
    """處理從熱門文章隨機設定推文任務的機器人類"""
    
    def get_today_hot_posts(self):
        """取得今日的熱門文章"""
        try:
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM ptt_aid_from_scraper
                WHERE DATE(created_at) = CURDATE()
                ORDER BY created_at DESC
            """)
            hot_posts = cursor.fetchall()
            cursor.close()
            
            print(f"找到 {len(hot_posts)} 篇今日熱門文章")
            return hot_posts
            
        except Error as e:
            print(f"查詢今日熱門文章時發生錯誤: {e}")
            self._connect_db()
            return []
    
    def get_random_template_id(self, board):
        """從 replay_template 表中隨機取得一個推文模板ID"""
        try:
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id 
                FROM replay_template 
                WHERE site = 'PTT' AND board = %s
                ORDER BY RAND() 
                LIMIT 1
            """, (board,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                template_id = result[0]
                print(f"隨機選擇推文模板ID: {template_id} (board: {board})")
                return template_id
            else:
                print(f"在 replay_template 表中未找到符合條件的模板 (site='PTT', board='{board}')")
                return None
                
        except Error as e:
            print(f"查詢推文模板時發生錯誤: {e}")
            self._connect_db()
            return None
    
    def check_existing_push_task(self, aid, board):
        """檢查是否已經存在相同的推文任務"""
        try:
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id FROM ptt_push_post 
                WHERE account_id = %s AND aid = %s AND board = %s
            """, (self.account_id, aid, board))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result is not None
            
        except Error as e:
            print(f"檢查推文任務時發生錯誤: {e}")
            self._connect_db()
            return True  # 發生錯誤時，假設已存在，避免重複建立
    
    def create_random_push_task(self):
        """從今日熱門文章中隨機創建一個推文任務"""
        try:
            # 取得今日熱門文章
            hot_posts = self.get_today_hot_posts()
            
            if not hot_posts:
                print("今日沒有熱門文章，無法創建推文任務")
                return False
            
            # 過濾掉已經有推文任務的文章
            available_posts = []
            for post in hot_posts:
                if not self.check_existing_push_task(post['aid'], post['board']):
                    available_posts.append(post)
            
            if not available_posts:
                print("今日熱門文章都已經有推文任務了")
                return False
            
            # 隨機選擇一篇文章
            selected_post = random.choice(available_posts)
            print(f"隨機選擇文章: board={selected_post['board']}, aid={selected_post['aid']}")
            
            # 取得隨機推文模板
            content_id = self.get_random_template_id(selected_post['board'])
            
            if not content_id:
                print(f"無法找到 {selected_post['board']} 板的推文模板")
                return False
            
            # 創建推文任務
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO ptt_push_post (account_id, board, aid, content_id) 
                VALUES (%s, %s, %s, %s)
            """, (self.account_id, selected_post['board'], selected_post['aid'], content_id))
            
            self.conn.commit()
            cursor.close()
            
            print(f"成功創建推文任務:")
            print(f"  - 帳號ID: {self.account_id}")
            print(f"  - 看板: {selected_post['board']}")
            print(f"  - 文章ID: {selected_post['aid']}")
            print(f"  - 模板ID: {content_id}")
            print(f"  - 文章URL: {selected_post['url']}")
            
            # 記錄活動
            self.log_activity(
                "創建推文任務", 
                True, 
                f"從熱門文章創建推文任務 - 看板: {selected_post['board']}, AID: {selected_post['aid']}, 模板ID: {content_id}"
            )
            
            return True
            
        except Error as e:
            print(f"創建推文任務時發生錯誤: {e}")
            if self.conn:
                self.conn.rollback()
            self._connect_db()
            return False
    
    def execute_random_push_setup(self):
        """執行隨機推文任務設定"""
        try:
            print(f"帳號 {self.account} 開始執行隨機推文任務設定...")
            
            # 檢查今日是否已經創建過推文任務
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM ptt_push_post 
                WHERE account_id = %s 
                AND DATE(COALESCE(push_time, NOW())) = CURDATE()
            """, (self.account_id,))
            
            today_count = cursor.fetchone()[0]
            cursor.close()
            
            if today_count > 0:
                print(f"帳號 {self.account} 今日已經有 {today_count} 個推文任務，跳過創建")
                return False
            
            # 創建隨機推文任務
            success = self.create_random_push_task()
            
            if success:
                print(f"帳號 {self.account} 成功創建隨機推文任務")
            else:
                print(f"帳號 {self.account} 創建隨機推文任務失敗")
                
            return success
            
        except Exception as e:
            print(f"執行隨機推文任務設定時發生錯誤: {e}")
            return False
    
    def get_pending_push_posts(self):
        """取得待執行的推文任務（status = null 且 account_id = 當前帳號）"""
        try:
            self._connect_db()  # 確保資料庫連接
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT pp.*, rt.content 
                FROM ptt_push_post pp
                JOIN replay_template rt ON pp.content_id = rt.id
                WHERE pp.account_id = %s 
                AND pp.status IS NULL
                ORDER BY pp.id ASC
            """, (self.account_id,))
            
            push_posts = cursor.fetchall()
            cursor.close()
            
            print(f"找到 {len(push_posts)} 個待執行的推文任務")
            return push_posts
            
        except Error as e:
            print(f"查詢待執行推文任務時發生錯誤: {e}")
            self._connect_db()
            return []
    
    def execute_push_post(self, push_post):
        """執行單個推文任務"""
        try:
            board = push_post['board']
            aid = push_post['aid']
            content = push_post['content']
            
            print(f"正在推文: 看板 {board}, 文章ID {aid}")
            print(f"推文內容: {content}")
            
            # 隨機等待 3-8 秒再推文，避免被系統偵測為機器人
            wait_time = random.uniform(3, 8)
            print(f"等待 {wait_time:.1f} 秒後推文...")
            time.sleep(wait_time)
            
            # 執行推文
            self.ptt_bot.comment(
                board=board,
                comment_type=PyPtt.CommentType.PUSH,
                content=content,
                aid=aid
            )
            
            # 更新推文狀態為完成
            self._connect_db()
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE ptt_push_post 
                SET status = 'completed', push_time = NOW()
                WHERE id = %s
            """, (push_post['id'],))
            
            self.conn.commit()
            cursor.close()
            
            print(f"推文成功: 看板 {board}, 文章ID {aid}")
            
            # 記錄活動
            self.log_activity(
                "執行推文", 
                True, 
                f"隨機推文任務 - 看板: {board}, AID: {aid}, 內容: {content}"
            )
            
            return True
            
        except Exception as e:
            error_message = str(e)
            print(f"推文失敗: {error_message}")
            
            # 更新推文狀態為失敗
            try:
                self._connect_db()
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE ptt_push_post 
                    SET status = 'failed', push_time = NOW()
                    WHERE id = %s
                """, (push_post['id'],))
                
                self.conn.commit()
                cursor.close()
            except:
                pass
            
            # 記錄失敗活動
            self.log_activity(
                "執行推文", 
                False, 
                f"隨機推文任務失敗 - 看板: {push_post['board']}, AID: {push_post['aid']}, 錯誤: {error_message}"
            )
            
            return False
    
    def execute_random_push_posts(self):
        """執行隨機推文任務"""
        try:
            print(f"帳號 {self.account} 開始執行隨機推文任務...")
            
            # 取得待執行的推文任務
            push_posts = self.get_pending_push_posts()
            
            if not push_posts:
                print(f"帳號 {self.account} 沒有待執行的推文任務")
                return 0
            
            successful_pushes = 0
            
            # 執行每個推文任務
            for push_post in push_posts:
                try:
                    success = self.execute_push_post(push_post)
                    if success:
                        successful_pushes += 1
                    
                    # 推文間隔，避免太頻繁
                    if push_post != push_posts[-1]:  # 不是最後一個
                        wait_time = random.uniform(5, 15)
                        print(f"推文間隔等待 {wait_time:.1f} 秒...")
                        time.sleep(wait_time)
                        
                except Exception as e:
                    print(f"執行推文任務時發生錯誤: {e}")
                    continue
            
            print(f"帳號 {self.account} 完成 {successful_pushes}/{len(push_posts)} 個推文任務")
            return successful_pushes
            
        except Exception as e:
            print(f"執行隨機推文任務時發生錯誤: {e}")
            return 0

def main():
    """主程式入口 - 支援獨立執行"""
    try:
        print("=== PTT 隨機推文任務設定程式 ===")
        
        # 連接資料庫取得第一個可用的 PTT 帳號
        import mysql.connector
        from config import DB_CONFIG
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT account, password 
            FROM accounts 
            WHERE status = 1 AND account_type = 'PTT' 
            ORDER BY id ASC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            print("沒有找到可用的 PTT 帳號")
            return False
        
        account, password = result
        print(f"使用帳號: {account}")
        
        # 創建隨機推文機器人
        bot = PttSetRandomPushBot(account, password)
        
        # 資料庫連接會在初始化時自動建立，但我們再檢查一次
        if not bot.conn or not bot.conn.is_connected():
            print("資料庫連接失敗")
            return False
        
        print(f"帳號ID: {bot.account_id}")
        
        if not bot.account_id:
            print("無法找到帳號ID")
            return False
        
        # 執行隨機推文任務設定
        setup_success = bot.execute_random_push_setup()
        
        if setup_success:
            print("隨機推文任務設定成功")
        else:
            print("隨機推文任務設定完成（可能今日已設定過或無可用文章）")
        
        # 執行隨機推文任務
        print("\n執行隨機推文任務...")
        push_count = bot.execute_random_push_posts()
        print(f"完成 {push_count} 個隨機推文任務")
        
        # 關閉資料庫連接
        if bot.conn:
            bot.conn.close()
        
        print(f"\n隨機推文程式執行完成！")
        print(f"- 任務設定: {'成功' if setup_success else '已完成或無可用文章'}")
        print(f"- 推文執行: {push_count} 個任務")
        
        return setup_success or push_count > 0
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
