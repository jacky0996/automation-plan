import asyncio
import mysql.connector
from datetime import datetime
from mysql.connector import Error
from cmoneyBase import CMoneyBase
from config import DB_CONFIG

class CMoneyPostBot(CMoneyBase):
    """專門處理 CMONEY 發文功能的類別"""
    
    def __init__(self, account, password):
        super().__init__(account, password)
        self.posts_processed = 0
        # 瀏覽器相關屬性 - 不再自己初始化，由外部傳入
        self.browser = None
        self.context = None
        self.page = None
    
    def execute_pending_posts(self):
        """執行待發布的文章任務 - 修正版本"""
        try:
            print("檢查 CMONEY 待發布的文章...")
            
            # 檢查是否有瀏覽器實例
            if not self.page:
                print("未找到瀏覽器實例，無法執行發文任務")
                return 0
            
            # 檢查瀏覽器是否仍然有效
            try:
                current_url = self.page.url
                print(f"當前頁面 URL: {current_url}")
            except Exception as e:
                print(f"瀏覽器實例無效: {e}")
                return 0
            
            # 直接使用 asyncio.run，不要檢查現有循環
            try:
                print("直接使用 asyncio.run 執行發文任務")
                result = asyncio.run(self._process_forum_posts())
                return result if result else 0
            except Exception as e:
                print(f"執行異步發文任務時出錯: {e}")
                return 0
            
        except Exception as e:
            print(f"執行 CMONEY 發文任務時出錯: {e}")
            self.log_activity("發文任務", False, f"執行發文任務出錯: {str(e)}")
            return 0
    
    async def _process_forum_posts(self):
        try:
            print("跳轉到股市同學會...")  
            # 修改 goto 方法，不等待所有資源載入完成
            await self.page.goto("https://www.cmoney.tw/forum/popular/buzz?tab=popular", 
                             wait_until="domcontentloaded", 
                             timeout=30000)
            
            print("成功跳轉到股市同學會")
            
            # 檢查 searchbar__input 是否存在 - 修改為最多檢查三次
            for attempt in range(3):  # 最多檢查三次
                try:
                    print(f"第 {attempt + 1} 次檢查搜尋欄位...")
                    search_input = await self.page.wait_for_selector(".searchbar__input", timeout=5000)
                    if search_input:
                        print("找到搜尋欄位")
                        break  # 找到就跳出循環
                except Exception as e:
                    print(f"第 {attempt + 1} 次檢查搜尋欄位失敗: {e}")
                    if attempt < 2:  # 如果不是最後一次嘗試
                        print("等待5秒後重試...")
                        await asyncio.sleep(5)
                    else:  # 如果是最後一次嘗試且失敗
                        print("三次嘗試都失敗，準備登出")
                        return -1  # 返回 -1 表示需要登出
        
            # 獲取並處理待發布文章
            posts_count = await self._process_pending_posts()
            return posts_count

        except Exception as e:
            print(f"處理發文任務時發生錯誤: {e}")
            self.log_activity("發文任務", False, f"處理發文任務錯誤: {str(e)}")
            return 0
    
    async def _find_search_input(self):
        """尋找搜尋欄位"""
        for i in range(3):
            try:
                search_input = await self.page.wait_for_selector(".searchbar__input", timeout=5000)
                if search_input:
                    print("找到搜尋欄位")
                    return True
            except Exception as e:
                print(f"第 {i+1} 次檢查搜尋欄位失敗: {e}")
                if i < 2:
                    print(f"第{i+1}次嘗試失敗，等待5秒後重試")
                    await asyncio.sleep(5)
                else:
                    print("三次嘗試都失敗，但登入成功，繼續執行")
        
        return False
    
    async def _process_pending_posts(self):
        """獲取並處理待發布的文章"""
        try:
            # 連接 MySQL 資料庫
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            cursor = conn.cursor(dictionary=True)  # 使用字典遊標
            
            # 查詢需要發文的文章
            cursor.execute("""
                SELECT id, board, title, content 
                FROM posts 
                WHERE account_id = %s AND platform = 'CMONEY' AND (result != 'success' OR result IS NULL)
            """, (self.account_id,)) 
            posts = cursor.fetchall()
            print(f"找到 {len(posts)} 篇待發文章")
            
            success_count = 0
            
            # 如果有文章需要發文
            if posts:
                for post in posts:
                    # 使用字典方式訪問結果集
                    post_id = post['id']
                    board = post['board']  
                    title = post['title']
                    content = post['content']
                    
                    # 處理單篇文章發布
                    post_success = await self._publish_post(post_id, board, title, content, conn, cursor)
                    if post_success:
                        success_count += 1
                        self.log_activity("發文", True, f"成功發布文章: {title}")
                    else:
                        self.log_activity("發文", False, f"發布文章失敗: {title}")
            else:
                print("沒有待發布的文章")
            
            # 關閉資料庫連接
            cursor.close()
            conn.close()
            
            print(f"CMONEY 發文任務完成: {success_count}/{len(posts)} 篇文章發布成功")
            self.posts_processed = success_count
            return success_count
            
        except Error as e:  # 使用 mysql.connector 的 Error
            print(f"處理發文過程中發生錯誤: {e}")
            # 如果資料庫連線存在則關閉
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()
            return 0
    
    async def _publish_post(self, post_id, board, title, content, conn, cursor):
        """發布單篇文章到指定看板"""
        print(f"處理看板: {board}, 文章: {title}")
        
        # 跳轉到指定看板
        click_success = await self._navigate_to_board(board)
        
        # 如果成功跳轉到目標看板
        if click_success:
            # 尋找並點擊發文按鈕
            post_success = await self._find_and_click_post_button(board, title, content)
            
            # 根據發文結果更新資料庫
            await self._update_post_result(post_id, post_success, title, conn, cursor)
            return post_success
        else:
            print(f"無法跳轉到目標看板 {board}，無法處理文章ID: {post_id}")
            # 更新文章狀態為失敗
            cursor.execute("""
                UPDATE posts 
                SET result = 'fail', result_message = %s 
                WHERE id = %s
            """, ("無法跳轉到指定看板", post_id))
            conn.commit()
            return False
    
    async def _navigate_to_board(self, board):
        """跳轉到指定看板"""
        try:
            # 構建看板 URL
            board_url = f"https://www.cmoney.tw/forum/stock/{board}"
            print(f"正在跳轉到看板 URL: {board_url}")
            
            # 增加跳轉超時時間到 30 秒
            await self.page.goto(board_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            
            # 檢查是否成功跳轉到目標看板
            current_url = self.page.url
            print(f"跳轉後的 URL: {current_url}")
            
            # 更靈活的檢查方式
            if f"/{board}" in current_url or board.lower() in current_url.lower():
                print(f"成功跳轉到目標看板: {current_url}")
                return True
            else:
                print(f"跳轉後的URL: {current_url}，不符合預期，將嘗試重新整理")
                await self.page.reload()
                await self.page.wait_for_load_state("networkidle", timeout=30000)
                
                # 再次檢查
                current_url = self.page.url
                if f"/{board}" in current_url or board.lower() in current_url.lower():
                    print(f"成功重新整理後跳轉到目標看板: {current_url}")
                    return True
                else:
                    # 即使URL不匹配，也可能已經在正確頁面，嘗試檢查頁面內容
                    try:
                        page_content = await self.page.content()
                        if board in page_content:
                            print(f"雖然URL不符合預期，但頁面內容包含看板代碼 {board}，嘗試繼續")
                            return True
                        else:
                            print(f"重新整理後的URL和頁面內容都不符合預期，將無法處理此文章")
                            return False
                    except:
                        print(f"檢查頁面內容失敗，將無法處理此文章")
                        return False
        except Exception as e:
            print(f"跳轉到看板 URL 時發生錯誤: {e}")
            
            # 即使跳轉失敗，仍嘗試檢查當前頁面
            try:
                current_url = self.page.url
                print(f"錯誤後當前 URL: {current_url}")
                
                # 如果URL包含股票代碼，可能實際上已經跳轉成功
                if f"/{board}" in current_url or board.lower() in current_url.lower():
                    print(f"儘管發生錯誤，但目前似乎已在目標看板: {current_url}")
                    return True
            except:
                pass
                
            # 嘗試直接重新加載頁面作為補救措施
            try:
                print("嘗試通過重新載入頁面來恢復...")
                await self.page.reload(timeout=30000)
                await asyncio.sleep(5)
                
                # 在重新載入後再次檢查
                current_url = self.page.url
                if f"/{board}" in current_url or board.lower() in current_url.lower():
                    print(f"重新載入後已在目標看板: {current_url}")
                    return True
            except:
                pass
            
            return False
    
    async def _find_and_click_post_button(self, board, title, content):
        """尋找並點擊發文按鈕，處理發文流程"""
        print(f"準備在 {board} 看板發表文章: {title}")
        post_success = False
        
        # 可能的發文按鈕選擇器列表
        post_btn_selectors = [
            ".post__text", 
        ]
        
        # 循環嘗試每個選擇器
        for selector in post_btn_selectors:
            for attempt in range(2):  # 每個選擇器嘗試兩次
                try:
                    print(f"嘗試使用選擇器 {selector} 查找發文按鈕...")
                    
                    # 等待按鈕出現
                    post_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    
                    if post_btn:
                        print(f"找到發文按鈕 ({selector})")
                        
                        # 點擊發文按鈕
                        await post_btn.click()
                        print(f"已點擊發文按鈕 ({selector})")
                        
                        # 處理發文模態框
                        if await self._handle_post_modal(title, content):
                            post_success = True
                            return post_success
                        
                        # 如果處理模態框失敗，繼續嘗試其他選擇器
                        print("處理發文視窗失敗，將嘗試其他選擇器")
                except Exception as e:
                    print(f"使用選擇器 {selector} 查找發文按鈕時出錯: {e}")
                    continue  # 嘗試下一個選擇器
            
            # 如果已經嘗試過所有選擇器仍然失敗，記錄錯誤並返回
            print(f"所有嘗試都失敗，無法找到發文按鈕: {title} 在看板: {board}")
            return False
        
        return post_success
    
    async def _handle_post_modal(self, title, content):
        """處理發文的模態框"""
        try:
            print("處理發文模態框...")
            
            # 等待內容編輯器加載
            await self.page.wait_for_selector(".messageModal__textarea", timeout=10000)
            
            # 填寫內容
            await self.page.fill(".messageModal__textarea", content)
            print("內容填寫完成")
            
            # 提交發文
            await self.page.click(".messageModal__submit")
            print("發文提交按鈕已點擊")
            
            # 等待發文結果反饋
            await self.page.wait_for_timeout(5000)  # 等待5秒以便發文處理
            
            # 檢查發文是否成功 - 修正版本
            post_url = self.page.url
            if "tab=discuss" in post_url:
                print(f"文章發表成功，當前頁面: {post_url}")
                return True
            else:
                print(f"發文後未檢測到 tab=discuss 參數，可能發文失敗。當前 URL: {post_url}")
                return False
            
        except Exception as e:
            print(f"處理發文模態框時發生錯誤: {e}")
            return False
    
    async def _update_post_result(self, post_id, success, title, conn, cursor):
        """更新文章發文結果"""
        try:
            if success:
                result_message = "成功"
                result_status = "success"
            else:
                result_message = "失敗"
                result_status = "fail"
            
            # 更新文章狀態
            cursor.execute("""
                UPDATE posts 
                SET result = %s, result_message = %s 
                WHERE id = %s
            """, (result_status, result_message, post_id))
            conn.commit()
            
            print(f"文章ID {post_id} 發文結果更新為: {result_status}")
        except Exception as e:
            print(f"更新文章ID {post_id} 發文結果時出錯: {e}")
    
    async def _retry_failed_posts(self):
        """重新嘗試發佈失敗的文章"""
        try:
            # 連接 MySQL 資料庫
            conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            cursor = conn.cursor(dictionary=True)  # 使用字典遊標
            
            # 查詢發佈失敗的文章
            cursor.execute("""
                SELECT id, board, title, content 
                FROM posts 
                WHERE account_id = %s AND site_name = 'CMONEY' AND result = 'fail'
                ORDER BY updated_at ASC
            """, (self.account_id,)) 
            failed_posts = cursor.fetchall()
            print(f"找到 {len(failed_posts)} 篇發佈失敗的文章")
            
            success_count = 0
            
            # 如果有文章需要重新發佈
            if failed_posts:
                for post in failed_posts:
                    # 使用字典方式訪問結果集
                    post_id = post['id']
                    board = post['board']  
                    title = post['title']
                    content = post['content']
                    
                    print(f"重新嘗試發佈文章: {title} (ID: {post_id})")
                    
                    # 處理單篇文章重新發佈
                    post_success = await self._publish_post(post_id, board, title, content, conn, cursor)
                    if post_success:
                        success_count += 1
                        self.log_activity("發文", True, f"重新發布文章成功: {title}")
                    else:
                        self.log_activity("發文", False, f"重新發布文章失敗: {title}")
            else:
                print("沒有發佈失敗的文章")
            
            # 關閉資料庫連接
            cursor.close()
            conn.close()
            
            print(f"CMONEY 重新發佈任務完成: {success_count}/{len(failed_posts)} 篇文章重新發布成功")
            return success_count
            
        except Error as e:  # 使用 mysql.connector 的 Error
            print(f"處理重新發佈過程中發生錯誤: {e}")
            # 如果資料庫連線存在則關閉
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()
            return 0
    
    def log_activity(self, action, success, message):
        """記錄活動日誌"""
        # 這裡可以擴展為真正的日誌記錄邏輯，例如寫入文件或發送到日誌伺服器
        status = "成功" if success else "失敗"
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action} - {status}: {message}")