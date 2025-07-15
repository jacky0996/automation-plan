import time
import random
import asyncio
import os
import mysql.connector
from mysql.connector import Error
from playwright.async_api import async_playwright
from loginManager import LoginManager
from datetime import datetime
from config import DB_CONFIG, HEADLESS_BROWSER

class CMoneyLoginBot(LoginManager):
    """
    CMoney網站自動登入機器人
    使用Playwright實現瀏覽器自動化
    """
    def __init__(self, account, password):
        # 調用父類初始化方法，設置站點名稱為'cmoney'
        super().__init__('cmoney', account, password)
        self.browser = None
        self.context = None
        self.page = None
    
    async def _init_browser(self):
        """初始化瀏覽器 - 優化資源使用"""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=HEADLESS_BROWSER,  # 使用設定檔中的參數
                args=[
                    '--disable-gpu',  # 停用 GPU 加速
                    '--disable-dev-shm-usage',  # 避免記憶體問題
                    '--disable-extensions',  # 停用擴充功能
                    '--no-sandbox',  # 在受限環境中避免沙箱問題
                    '--disable-setuid-sandbox',
                    '--mute-audio'  # 關閉音效
                ]
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.page = await self.context.new_page()
            # 設定頁面超時時間
            self.page.set_default_timeout(60000)  # 設置為 60 秒
    
    async def _close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            print('關閉瀏覽器')
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    def _remove_lock_file(self):
        """移除登入鎖定檔案"""
        try:
            lock_file = f"{self.account}.lock"
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception as e:
            print(f"移除鎖定檔案時發生錯誤：{str(e)}")
    
    def login(self):
        """執行CMoney網站登入流程"""
        try:
            # 為當前線程創建新的事件循環
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._login_async())
                return result
            finally:
                loop.close()
        except Exception as e:
            print(f"CMoney 登入發生未預期錯誤：{str(e)}")
            self.log_login_attempt("失敗", f"未預期錯誤：{str(e)}")
            return False
        finally:
            self._remove_lock_file()
    
    def logout(self):
        """執行CMoney網站登出流程"""
        # 為當前線程創建新的事件循環
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._logout_async())
        finally:
            loop.close()
    
    def __del__(self):
        """確保完全釋放所有資源"""
        try:
            if hasattr(self, 'browser') and self.browser:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # 直接關閉瀏覽器，不執行登出操作
                    loop.run_until_complete(self._close_browser())
                    print("在物件銷毀時釋放瀏覽器資源")
                finally:
                    loop.close()
        except Exception as e:
            print(f"釋放資源時發生錯誤: {e}")
        
        # 確保調用父類的析構函數
        super().__del__()
    
    async def _login_async(self):
        """異步執行登入流程 - 添加 account_id 設置"""
        print('開始在 CMoney 首頁尋找會員登入按鈕')
        member_found = False  # 在方法開始處定義變量
        
        try:
            # 初始化瀏覽器
            await self._initialize_browser_with_retry()
            
            # 訪問應用頁面
            if not await self._navigate_to_app_page():
                return False
            
            # 點擊會員登入按鈕
            if not await self._click_login_button():
                return False
            
            # 執行登入操作
            if not await self._perform_login():
                return False
            
            # 處理雙重認證頁面
            member_found = await self._handle_two_factor_auth()
            
            # 最終檢查登入結果
            current_url = self.page.url
            if ("login" not in current_url and ("member" in current_url or "/" == current_url)) or member_found:
                # 登入成功
                print("登入成功")
                self.log_login_attempt("成功")
                
                # 處理發文任務
                await self._process_forum_posts()
                return True
            else:
                # 檢查是否有錯誤訊息
                try:
                    error_message = await self.page.inner_text(".error-message")
                    print(f"登入失敗，錯誤訊息: {error_message}")
                    self.log_login_attempt("失敗", f"登入失敗：{error_message}")
                except:
                    print("登入失敗，無法確定原因")
                    self.log_login_attempt("失敗", "登入失敗，無法確定原因")
                return False
                
        except Exception as e:
            # 發生異常
            error_msg = f"登入過程發生異常: {str(e)}"
            print(error_msg)
            self.log_login_attempt("失敗", error_msg)
            return False
        finally:
            # 不在這裡關閉瀏覽器，讓logout方法或構析函數處理
            pass
    
    async def _initialize_browser_with_retry(self):
        """初始化瀏覽器並處理可能的錯誤"""
        try:
            await self._init_browser()
            if not self.browser or not self.page:
                print("瀏覽器初始化失敗")
                return False
            return True
        except Exception as e:
            print(f"瀏覽器初始化錯誤: {e}")
            return False
    
    async def _navigate_to_app_page(self):
        """訪問CMoney應用頁面，包含重試機制"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                response = await self.page.goto("https://www.cmoney.tw/app/", timeout=60000)
                if response and response.ok:
                    print(f"訪問應用頁面成功")
                    return True
                
                print(f"訪問應用頁面失敗: {response.status if response else 'No response'}")
                retry_count += 1
                
                if retry_count < max_retries:
                    print(f"等待10秒後重試... (第{retry_count}次重試)")
                    await asyncio.sleep(10)
                else:
                    print("已達最大重試次數，無法訪問應用頁面")
                    await self._close_browser()
                    return False
            except Exception as e:
                print(f"訪問應用頁面時發生錯誤: {e}")
                retry_count += 1
                
                if retry_count < max_retries:
                    print(f"等待10秒後重試... (第{retry_count}次重試)")
                    await asyncio.sleep(10)
                else:
                    print("已達最大重試次數，無法訪問應用頁面")
                    await self._close_browser()
                    return False
        
        return False
    
    async def _click_login_button(self):
        """尋找並點擊會員登入按鈕"""
        selector_found = False
        retry_count = 0
        max_retries = 3
        
        while not selector_found and retry_count < max_retries:
            try:
                print(f"嘗試等待會員登入按鈕 #{retry_count+1}")
                login_button = await self.page.wait_for_selector(".cm-blackbar__headerMemberLinkText", timeout=5000)
                print(f"找到會員登入按鈕: {login_button}")
                
                # 點擊會員登入按鈕
                await login_button.click()
                print("已點擊會員登入按鈕")
                
                # 等待頁面跳轉
                await self.page.wait_for_load_state("networkidle")
                print(f"當前頁面URL: {self.page.url}")
                
                selector_found = True
                return True
            except Exception as e:
                print(f"等待會員登入按鈕失敗: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print("等待5秒後重試...")
                    await asyncio.sleep(5)
                else:
                    print("已達最大重試次數，無法找到會員登入按鈕")
                    await self._close_browser()
                    return False
        
        return selector_found
    
    async def _perform_login(self):
        """執行登入操作：填寫帳號密碼並點擊登入按鈕"""
        max_retries = 3
        retry_count = 0
        login_button_found = False
        
        while not login_button_found and retry_count < max_retries:
            try:
                print(f"嘗試等待登入按鈕 #{retry_count+1}")
                login_button = await self.page.wait_for_selector("#Login", timeout=5000)
                print(f"找到登入按鈕: {login_button}")
                login_button_found = True
                
                # 模擬人為操作，隨機等待1-3秒
                await asyncio.sleep(random.uniform(1, 3))
                
                # 輸入帳號
                await self.page.fill("#Account", self.account)
                print('帳號：', self.account, '輸入完畢')
                # 模擬人為操作，隨機等待0.5-1.5秒
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # 輸入密碼
                await self.page.fill("#Password", self.password)
                print('密碼：', self.password, '輸入完畢')
                # 模擬人為操作，隨機等待0.5-1.5秒
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # 點擊登入按鈕
                await self.page.click("#Login")
                print('點擊登入')
                # 等待登入結果
                await asyncio.sleep(5)  # 等待登入處理
                
                # 檢查登入結果
                current_url = self.page.url
                
                # 檢查是否在登入頁面或有錯誤訊息
                if "/identity/account/login" in current_url:
                    try:
                        # 檢查頁面是否包含錯誤訊息
                        page_content = await self.page.content()
                        if "帳號或密碼錯誤，請重新輸入或註冊" in page_content:
                            print("登入失敗：帳號或密碼錯誤")
                            self.log_login_attempt("失敗", "帳號或密碼錯誤")
                            await self._close_browser()
                            return False
                    except Exception as e:
                        print(f"檢查錯誤訊息時發生異常: {e}")
                        await self._close_browser()
                        return False
                
                return True
            except Exception as e:
                print(f"等待登入按鈕失敗: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print("等待5秒後重試...")
                    await asyncio.sleep(5)  # 等待5秒後重試
                else:
                    print("已達最大重試次數，無法找到登入按鈕")
                    await self._close_browser()
                    return False
        
        return login_button_found
    
    async def _handle_two_factor_auth(self):
        """處理可能出現的雙重認證頁面"""
        member_found = False
        try:
            page_content = await self.page.content()
            if "透過雙重認證保護您的帳戶" in page_content:
                if "帳號或密碼錯誤，請重新輸入或註冊" in page_content:
                    print("登入失敗：帳號或密碼錯誤")
                    self.log_login_attempt("失敗", "帳號或密碼錯誤")
                    return False
                
                print("檢測到雙重認證提示頁面")
                try:
                    skip_button = await self.page.wait_for_selector(".btn-pure", timeout=5000)
                    if skip_button:
                        print("找到跳過按鈕，點擊跳過雙重認證")
                        await skip_button.click()
                        await self.page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)
                        
                        # 更新當前URL並多次檢查
                        member_found = await self._check_member_page()
                except Exception as e:
                    print(f"尋找或點擊跳過按鈕時出錯: {e}")
            return member_found
        except Exception as e:
            print(f"檢查雙重認證頁面時出錯: {e}")
            return False
    
    async def _check_member_page(self):
        """檢查是否成功進入會員頁面"""
        member_found = False
        check_count = 0
        max_checks = 3
        
        while not member_found and check_count < max_checks:
            current_url = self.page.url
            print(f"檢查 #{check_count+1} - 當前頁面URL: {current_url}")
            
            if "member" in current_url:
                print("檢測到member字眼，登入成功")
                member_found = True
            else:
                check_count += 1
                if check_count < max_checks:
                    print(f"未檢測到member字眼，等待5秒後重新檢查 (剩餘 {max_checks - check_count} 次)")
                    await asyncio.sleep(5)  # 等待5秒後重新檢查
                else:
                    print("已達最大檢查次數，仍未檢測到member字眼，嘗試重新導向到會員頁面")
                    # 檢查三次失敗後重新導向到會員頁面
                    await self.page.goto("https://www.cmoney.tw/member/")
                    print("已重新導向到會員頁面")
                    
                    # 檢查頁面是否包含'會員資料'字樣
                    member_found = await self._check_member_info()
        
        return member_found
    
    async def _check_member_info(self):
        """檢查頁面是否包含會員資料字樣"""
        member_info_found = False
        check_count = 0
        max_checks = 3
        
        while check_count < max_checks:
            try:
                page_content = await self.page.content()
                if "會員資料" in page_content:
                    member_info_found = True
                    print("檢測到'會員資料'字樣，確認登入成功")
                    break
                else:
                    check_count += 1
                    if check_count < max_checks:
                        print(f"未檢測到'會員資料'字樣，等待5秒後重新檢查 (剩餘 {max_checks - check_count} 次)")
                        await asyncio.sleep(5)  # 等待5秒後重新檢查
                    else:
                        print("已達最大檢查次數，仍未檢測到'會員資料'字樣，確認登入失敗")
            except Exception as e:
                print(f"檢查頁面內容時出錯: {e}")
                check_count += 1
                if check_count < max_checks:
                    await asyncio.sleep(5)  # 等待5秒後重新檢查
                else:
                    print("已達最大檢查次數，檢查過程出錯")
        
        return member_info_found
    
    async def _process_forum_posts(self):
        """處理股市同學會發文任務"""
        try:
            print("跳轉到股市同學會...")
            await self.page.goto("https://www.cmoney.tw/forum/popular/buzz?tab=popular", timeout=60000)
            await self.page.wait_for_load_state("networkidle")
            print("成功跳轉到股市同學會")
            
            # 檢查 searchbar__input 是否存在
            search_input = await self._find_search_input()
            if not search_input:
                return False
            
            # 獲取並處理待發布文章
            await self._process_pending_posts()
            return True
            
        except Exception as e:
            print(f"處理發文任務時發生錯誤: {e}")
            return False
    
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
                WHERE account_id = %s AND (result != 'success' OR result IS NULL)
            """, (self.account_id,)) 
            posts = cursor.fetchall()
            print(f"找到 {len(posts)} 篇待發文章")
            
            # 如果有文章需要發文
            if posts:
                for post in posts:
                    # 使用字典方式訪問結果集
                    post_id = post['id']
                    board = post['board']  
                    title = post['title']
                    content = post['content']
                    
                    # 處理單篇文章發布
                    await self._publish_post(post_id, board, title, content, conn, cursor)
            else:
                print("沒有待發布的文章")
            
            # 關閉資料庫連接
            cursor.close()
            conn.close()
            
        except Error as e:  # 使用 mysql.connector 的 Error
            print(f"處理發文過程中發生錯誤: {e}")
            # 如果資料庫連線存在則關閉
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()
    
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
        else:
            print(f"無法跳轉到目標看板 {board}，無法處理文章ID: {post_id}")
            # 更新文章狀態為失敗
            cursor.execute("""
                UPDATE posts 
                SET result = 'fail', result_message = %s 
                WHERE id = %s
            """, ("無法跳轉到指定看板", post_id))
            conn.commit()
    
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
            ".post__btn", 
            "button:has-text('發表文章')",
            "button:has-text('發表')",
            "a:has-text('發表文章')",
            ".forum-list__addPost",
            ".forum-stock__addPost",
            "[class*='post']"
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
                        print("處理發文視窗失敗，嘗試其他選擇器...")
                        break
                        
                except Exception as e:
                    print(f"使用選擇器 {selector} 第 {attempt+1} 次嘗試失敗: {e}")
                    
                    # 第一次嘗試失敗後等待 5 秒再試
                    if attempt == 0:
                        await asyncio.sleep(5)
    
        # 如果所有選擇器都失敗，記錄錯誤並截圖
        print("所有嘗試都失敗，無法找到發文按鈕")
        try:
            # 截取當前頁面，幫助調試
            await self.page.screenshot(path=f"failed_post_{board}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            print(f"已保存頁面截圖")
        except:
            pass
        
        return post_success
    
    async def _handle_post_modal(self, title, content):
        """處理發文模態視窗"""
        modal_success = False
        
        # 等待一段時間讓模態框完全顯示
        await asyncio.sleep(5)
        
        # 可能的輸入框和按鈕選擇器組合
        form_selectors = [
            # 元組形式：(標題輸入框, 內容輸入框, 提交按鈕)
            (".messageModal__title input", ".messageModal__textarea", ".messageModal__submit"),
            ("input[placeholder*='標題']", "textarea", "button[type='submit']"),
            ("input[type='text']", "textarea", "button:has-text('發表')"),
            ("input[type='text']", "div[contenteditable='true']", "button:has-text('發表')"),
            (None, "textarea", "button:has-text('發表')"),  # 有些視窗可能沒有標題輸入框
            ("input[type='text']", "textarea", "button:has-text('送出')"),
            (".title-input", ".content-input", ".submit-btn")
        ]
        
        # 循環嘗試每個選擇器組合
        for selector_set in form_selectors:
            title_selector, content_selector, submit_selector = selector_set
            
            try:
                print(f"嘗試使用選擇器組合: {selector_set}")
                
                # 檢查內容輸入框和提交按鈕
                content_input = await self.page.wait_for_selector(content_selector, timeout=5000)
                submit_btn = await self.page.wait_for_selector(submit_selector, timeout=5000)
                
                if content_input and submit_btn:
                    print(f"找到內容輸入框和提交按鈕")
                    
                    # 如果有標題輸入框選擇器且不為 None
                    if title_selector:
                        try:
                            title_input = await self.page.wait_for_selector(title_selector, timeout=3000)
                            if title_input:
                                await title_input.fill(title)
                                print(f"已填入標題: {title}")
                        except Exception as title_error:
                            print(f"填入標題時出錯 (可能沒有標題欄位): {title_error}")
                    
                    # 填入文章內容
                    await content_input.fill(content)
                    print(f"已填入內容: {content[:30]}...")
                    
                    # 點擊提交按鈕
                    await submit_btn.click()
                    print("已點擊提交按鈕")
                    
                    # 等待提交完成
                    await asyncio.sleep(5)
                    
                    # 檢查是否有成功訊息
                    try:
                        success_message = await self.page.query_selector(".toast-success, .success-message, .alert-success")
                        if success_message:
                            text = await success_message.text_content()
                            print(f"發現成功訊息: {text}")
                        else:
                            print("未找到明確的成功訊息，但提交操作已完成")
                    except:
                        print("未找到明確的成功訊息，但提交操作已完成")
                    
                    modal_success = True
                    break  # 成功找到視窗並發文，跳出迴圈
                    
                else:
                    print("未找到完整的發文視窗元素")
        
            except Exception as modal_error:
                print(f"使用選擇器組合時出錯: {modal_error}")
            
        if not modal_success:
            print("所有嘗試都無法成功處理發文視窗")
            
            # 檢查是否出現錯誤訊息
            try:
                error_message = await self.page.query_selector(".toast-error, .error-message, .alert-danger")
                if error_message:
                    text = await error_message.text_content()
                    print(f"發現錯誤訊息: {text}")
            except:
                pass
        
        return modal_success
    
    async def _update_post_result(self, post_id, post_success, title, conn, cursor):
        """更新文章發布結果到資料庫"""
        if post_success:
            print(f"文章「{title}」發表成功")
            # 更新文章狀態
            cursor.execute("""
                UPDATE posts 
                SET result = 'success', post_time = %s 
                WHERE id = %s
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), post_id))
            conn.commit()
        else:
            print(f"未能成功發表文章「{title}」")
            # 更新文章狀態為失敗 - 修改欄位名稱從 error_message 到 result_message
            cursor.execute("""
                UPDATE posts 
                SET result = 'fail', result_message = %s 
                WHERE id = %s
            """, ("嘗試發文操作失敗", post_id))
            conn.commit()
    
    async def _logout_async(self):
        """異步執行登出流程，直接記錄登出時間並釋放資源"""
        try:
            if not self.browser or not self.page:
                print("瀏覽器未初始化或已關閉，無需額外處理")
                return True
            
            print("執行 CMoney 登出操作")
            
            # 記錄登出時間
            logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"登出時間: {logout_time}")
            
            # 記錄登出到數據庫
            try:
                conn = mysql.connector.connect(
                    host=DB_CONFIG['host'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    database=DB_CONFIG['database']
                )
                cursor = conn.cursor()
                
                # 更新登入日誌表中的登出時間
                cursor.execute("""
                    UPDATE login_logs 
                    SET logout_time = %s
                    WHERE account_id = %s AND site_name = 'cmoney' AND logout_time IS NULL
                    ORDER BY login_time DESC LIMIT 1
                """, (logout_time, self.account_id))
                
                conn.commit()
                cursor.close()
                conn.close()
                print(f"已將登出時間 {logout_time} 更新至資料庫")
            except Exception as db_error:
                print(f"更新登出時間到資料庫時出錯: {db_error}")
            
            return True
        except Exception as e:
            print(f"登出過程發生錯誤: {e}")
            return False
        finally:
            # 直接釋放瀏覽器資源
            try:
                print("釋放瀏覽器資源...")
                await self._close_browser()
                print("瀏覽器資源已釋放")
            except Exception as close_error:
                print(f"釋放瀏覽器資源時發生錯誤: {close_error}")