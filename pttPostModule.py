import time
import random
from mysql.connector import Error
from pttBase import PttBaseBot
import datetime

class PttPostBot(PttBaseBot):
    """處理 PTT 發文功能的機器人類"""
    
    def check_pending_posts(self):
        """檢查待處理的發文任務"""
        try:
            # 查詢未成功發文的任務
            print("檢查待發文項目...")
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, board, title, content, category 
                FROM posts 
                WHERE account_id = %s AND (result != 'success' OR result IS NULL)
                AND platform = 'ptt'
                ORDER BY post_time ASC
            """, (self.account_id,))
            pending_posts = cursor.fetchall()
            
            if pending_posts:
                print(f"找到 {len(pending_posts)} 個待發文項目")
            else:
                print("沒有待發文項目")
                
            return pending_posts
                
        except Error as e:
            print(f"檢查發文任務時發生錯誤: {e}")
            self._connect_db()
            return []

    def post_article(self, board, title, content, title_index, post_id=None):
        """發表文章"""
        try:
            print(f"正在發表文章: 看板 {board}, 標題 {title}")
            
            # 隨機等待 3-8 秒再發文，避免被系統偵測為機器人
            wait_time = random.uniform(3, 8)
            print(f"等待 {wait_time:.1f} 秒後發文...")
            time.sleep(wait_time)
            
            # 發表文章 - 注意：post 不會返回任何參數
            self.ptt_bot.post(
                board=board,
                title=title,
                content=content,
                title_index=int(title_index),
            )
            
            print("文章已發送，等待獲取文章 ID...")
            
            # 使用爬蟲方式獲取文章 ID
            article_id = None
            article_url = None
            
            import PyPtt  # 確保導入 PyPtt 以使用搜尋類型常量
            
            # 最多嘗試 3 次獲取文章 ID
            max_retries = 3
            for retry in range(max_retries):
                try:
                    print(f"嘗試獲取文章ID (第 {retry+1} 次)...")
                    
                    # 等待一段時間，確保文章已被系統處理
                    wait_time = 3 * (retry + 1)  # 等待時間遞增：3秒、6秒、9秒
                    print(f"等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    
                    # 使用官方提供的搜尋方法
                    # 設定搜尋條件：作者搜尋 + 關鍵字搜尋
                    search_list = [
                        (PyPtt.SearchType.AUTHOR, self.account),  # 搜尋作者
                        (PyPtt.SearchType.KEYWORD, title)  # 搜尋文章標題
                    ]
                    
                    try:
                        # 使用搜尋列表獲取最新文章索引
                        newest_index = self.ptt_bot.get_newest_index(
                            PyPtt.NewIndex.BOARD,
                            board,
                            search_list=search_list
                        )
                        print(f"使用搜尋條件獲取到的最新文章索引: {newest_index}")
                        
                        if newest_index > 0:
                            # 獲取指定索引的文章 - 正確傳入 search_list 參數
                            post_detail = self.ptt_bot.get_post(
                                board=board,
                                index=newest_index,
                                search_list=search_list  # 添加這個參數
                            )
                            
                            if post_detail:
                                print(f"獲取到的文章詳情: {post_detail.get('title', '無標題')}")
                                
                                # 檢查是否是自己發的文章
                                author = post_detail.get('author', '')
                                if author and self.account in author:
                                    # 找到了自己的文章
                                    article_id = post_detail.get('aid')
                                    if not article_id:
                                        article_id = post_detail.get('AID')
                                    
                                    if article_id:
                                        article_url = f"https://www.ptt.cc/bbs/{board}/{article_id}.html"
                                        print(f"找到文章: {post_detail.get('title')} (ID: {article_id})")
                                        break
                                    else:
                                        print("找到文章但無法獲取 ID")
                                else:
                                    print(f"找到的文章不是由 {self.account} 發布的，作者: {author}")
                            else:
                                print("獲取到的文章詳情為空")
                        else:
                            print("未找到符合搜尋條件的文章")
                            
                            # 嘗試獲取該板最新的幾篇文章
                            try:
                                print("嘗試直接獲取版面最新文章...")
                                
                                # 獲取前 5 篇文章
                                post_list = self.ptt_bot.get_post_list(board=board, max_post=5)
                                
                                if post_list:
                                    for post_item in post_list:
                                        post_title = post_item.get('title', '')
                                        post_author = post_item.get('author', '')
                                        
                                        print(f"檢查文章: {post_title} by {post_author}")
                                        
                                        # 檢查是否是自己發的文章
                                        if post_author and self.account in post_author and title in post_title:
                                            post_index = post_item.get('index')
                                            
                                            # 獲取完整文章
                                            full_post = self.ptt_bot.get_post(
                                                board=board,
                                                index=post_index,
                                                search_list=search_list  # 添加這個參數
                                            )
                                            
                                            if full_post:
                                                article_id = full_post.get('aid')
                                                if not article_id:
                                                    article_id = full_post.get('AID')
                                                
                                                if article_id:
                                                    article_url = f"https://www.ptt.cc/bbs/{board}/{article_id}.html"
                                                    print(f"找到文章: {post_title} (ID: {article_id})")
                                                    break
                            except Exception as list_error:
                                print(f"獲取版面文章列表時出錯: {list_error}")
                                    
                    except Exception as search_error:
                        print(f"搜尋文章時發生錯誤: {search_error}")
                        
                except Exception as retry_error:
                    print(f"第 {retry+1} 次嘗試獲取文章ID時出錯: {retry_error}")
        
            # 如果仍然無法獲取文章ID，生成一個臨時ID
            if not article_id:
                # 生成一個基於時間的臨時ID
                article_id = f"unknown_{int(time.time())}"
                article_url = f"https://www.ptt.cc/bbs/{board}/{article_id}.html"
                print(f"無法獲取真實文章ID，使用臨時ID: {article_id}")
            else:
                print(f"文章發表成功! 文章ID: {article_id}")
            
            # 如果提供了 post_id，更新資料庫中的文章狀態
            if post_id:
                # 獲取包含毫秒的當前時間
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE posts 
                    SET result = 'success', 
                        article_id = %s,
                        article_url = %s,
                        post_time = %s
                    WHERE id = %s
                """, (article_id, article_url, current_time, post_id))
                self.conn.commit()
                
            # 記錄發文活動
            self.log_activity(
                "發文", 
                True, 
                f"看板: {board}, 標題: {title}, 文章ID: {article_id}"
            )
            
            return article_id
        
        except Exception as e:
            error_message = str(e)
            print(f"發文失敗: {error_message}")
            
            # 如果提供了 post_id，更新資料庫中的文章狀態為失敗
            if post_id:
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE posts 
                    SET result = 'fail',
                        result_message = %s
                    WHERE id = %s
                """, (error_message, post_id))
                self.conn.commit()
                
            # 記錄失敗活動
            self.log_activity(
                "發文", 
                False, 
                f"看板: {board}, 標題: {title}, 錯誤: {error_message}"
            )
            
            return None

    def execute_pending_posts(self):
        """執行所有待處理的發文任務"""
        pending_posts = self.check_pending_posts()
        successful_posts = 0
        
        for post in pending_posts:
            try:
                result = self.post_article(
                    board=post['board'],
                    title=post['title'],
                    title_index=post['category'],
                    content=post['content'],
                    post_id=post['id']
                )
                
                if result:
                    successful_posts += 1
                    
                # 兩篇文章間隔至少 3 分鐘，避免洗版
                if successful_posts > 0 and post != pending_posts[-1]:
                    wait_time = random.uniform(180, 300)  # 3-5 分鐘
                    print(f"發文間隔等待 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"執行發文任務時發生錯誤: {e}")
        
        return successful_posts