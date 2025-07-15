import PyPtt
import time
import random
import datetime
from mysql.connector import Error
from pttBase import PttBaseBot

class PttPushBot(PttBaseBot):
    """處理 PTT 推文功能的機器人類"""
    
    def check_and_create_push_tasks(self):
        """檢查並創建推文任務"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # 計算三天前的日期
            three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
            
            # 查找其他帳號成功發布的文章，且當前帳號尚未推文的，且文章發布時間不超過三天
            cursor.execute("""
                SELECT p.id, p.board, p.article_id, p.account_id, p.post_time
                FROM posts p
                WHERE p.result = 'success' 
                AND p.article_id IS NOT NULL
                AND p.account_id != %s
                AND p.post_time >= %s
                AND NOT EXISTS (
                    SELECT 1 
                    FROM push_tasks pt
                    WHERE pt.account_id = %s
                    AND pt.post_id = p.id
                    AND pt.status = 'completed'
                )
            """, (self.account_id, three_days_ago, self.account_id))
            
            unpushed_posts = cursor.fetchall()
            
            # 為每個未推文的文章建立推文任務
            for post in unpushed_posts:
                cursor.execute("""
                    INSERT INTO push_tasks 
                    (account_id, post_id, board, article_id, status, created_at, push_content)
                    VALUES (%s, %s, %s, %s, 'pending', NOW(), %s)
                    ON DUPLICATE KEY UPDATE 
                    status = IF(status = 'failed', 'pending', status)
                """, (
                    self.account_id,
                    post['id'],
                    post['board'],
                    post['article_id'],
                    '推'  # 設定默認的推文內容
                ))
                
            self.conn.commit()
            
            if unpushed_posts:
                print(f"已為當前帳號 {self.account} 創建 {len(unpushed_posts)} 個推文任務")
            return len(unpushed_posts)
            
        except Error as e:
            print(f"檢查推文任務時發生錯誤: {e}")
            self._connect_db()
            return 0

    def execute_push_tasks(self):
        """執行推文任務"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # 計算三天前的日期
            three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
            
            # 獲取待處理的推文任務，只選擇三天內創建的任務
            cursor.execute("""
                SELECT pt.*, a.account as target_account 
                FROM push_tasks pt
                JOIN posts p ON pt.post_id = p.id
                JOIN accounts a ON p.account_id = a.id
                WHERE pt.account_id = %s 
                AND pt.status = 'pending'
                AND pt.created_at >= %s
                ORDER BY pt.created_at ASC
            """, (self.account_id, three_days_ago))
            
            push_tasks = cursor.fetchall()
            
            if push_tasks:
                print(f"找到 {len(push_tasks)} 個待處理的推文任務")
            
            successful_pushes = 0
            
            for task in push_tasks:
                try:
                    print(f"正在推文: 看板 {task['board']}, 文章ID {task['article_id']}, 作者 {task['target_account']}")
                    
                    # 隨機等待 5-15 秒再推文，避免被系統偵測為機器人
                    wait_time = random.uniform(5, 15)
                    print(f"等待 {wait_time:.1f} 秒後推文...")
                    time.sleep(wait_time)
                    
                    # 執行推文，使用 comment API
                    self.ptt_bot.comment(
                        board=task['board'],
                        comment_type=PyPtt.CommentType.PUSH,
                        content=task['push_content'],  # 使用資料庫中的推文內容
                        aid=task['article_id']
                    )
                    
                    # 更新任務狀態
                    cursor.execute("""
                        UPDATE push_tasks 
                        SET status = 'completed',
                            completed_at = NOW()
                        WHERE id = %s
                    """, (task['id'],))
                    
                    # 記錄推文活動
                    self.log_activity(
                        "推文", 
                        True, 
                        f"看板: {task['board']}, 文章ID: {task['article_id']}, 作者: {task['target_account']}"
                    )
                    
                    print(f"推文成功: 看板 {task['board']}, 文章ID {task['article_id']}")
                    successful_pushes += 1
                    
                except Exception as push_error:
                    # 更新任務狀態為失敗
                    cursor.execute("""
                        UPDATE push_tasks 
                        SET status = 'failed',
                            error_message = %s
                        WHERE id = %s
                    """, (str(push_error), task['id']))
                    
                    self.log_activity(
                        "推文", 
                        False, 
                        f"看板: {task['board']}, 文章ID: {task['article_id']}, 錯誤: {str(push_error)}"
                    )
                    
                    print(f"推文失敗: {str(push_error)}")
                
                self.conn.commit()
                
            return successful_pushes
                
        except Error as e:
            print(f"執行推文任務時發生錯誤: {e}")
            self._connect_db()
            return 0

    def push_article(self, board, article_id, push_content):
        """推文特定文章"""
        try:
            print(f"正在推文: 看板 {board}, 文章ID {article_id}")
            
            self.ptt_bot.comment(
                board=board,
                comment_type=PyPtt.CommentType.PUSH,
                content=push_content,
                aid=article_id
            )
            
            print(f"推文成功: 看板 {board}, 文章ID {article_id}")
            return True
        
        except Exception as e:
            print(f"推文失敗: {e}")
            return False