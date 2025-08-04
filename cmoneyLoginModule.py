import time
import asyncio
import random
import mysql.connector
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from cmoneyBase import CMoneyBase
from config import DB_CONFIG, HEADLESS_BROWSER 
class CMoneyLoginBot(CMoneyBase):
    """專門處理 CMONEY 登入/登出功能的類別"""
    
    def __init__(self, account, password):
        super().__init__(account, password)
        self.is_login = False
        self.log_id = None
        # 瀏覽器相關屬性
        self.browser = None
        self.context = None
        self.page = None
        # 保存 playwright 實例
        self.playwright = None

    async def _init_browser(self):
        """初始化瀏覽器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=HEADLESS_BROWSER)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            return True
        except Exception as e:
            print(f"初始化瀏覽器失敗: {e}")
            return False
    
    async def _close_browser(self):
        """關閉瀏覽器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"關閉瀏覽器時出錯: {e}")

    def login(self):
        """執行 CMONEY 登入流程 - 保持事件循環"""
        try:
            print(f"準備登入 CMONEY 帳號: {self.account}")
            
            # 創建事件循環但不在 finally 中關閉
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self._login_async())
                
                if result:
                    print("登入成功，保持事件循環供發文使用")
                    # 將循環保存起來，供後續使用
                    self._current_loop = loop
                    return True
                else:
                    loop.close()
                    return False
                    
            except Exception as e:
                print(f"執行登入時出錯: {e}")
                loop.close()
                return False
            
        except Exception as e:
            print(f"CMONEY 登入發生錯誤：{str(e)}")
            self._log_login_attempt("失敗", f"登入錯誤：{str(e)}")
            self.log_activity("登入", False, f"登入錯誤：{str(e)}")
            return False
        finally:
            self._remove_lock_file()

    async def _login_async(self):
        """異步執行登入流程 - 使用您原本的登入機制"""
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
                self._log_login_attempt("成功", "CMONEY 登入成功")
                self.log_activity("登入", True, "CMONEY 登入成功")
                
                self.is_login = True
                return True
            else:
                # 檢查是否有錯誤訊息
                try:
                    error_message = await self.page.inner_text(".error-message")
                    print(f"登入失敗，錯誤訊息: {error_message}")
                    self._log_login_attempt("失敗", f"登入失敗：{error_message}")
                    self.log_activity("登入", False, f"登入失敗：{error_message}")
                except:
                    print("登入失敗，無法確定原因")
                    self._log_login_attempt("失敗", "登入失敗，無法確定原因")
                    self.log_activity("登入", False, "登入失敗，無法確定原因")
                return False
                
        except Exception as e:
            # 發生異常
            error_msg = f"登入過程發生異常: {str(e)}"
            print(error_msg)
            self._log_login_attempt("失敗", error_msg)
            self.log_activity("登入", False, error_msg)
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
                            self._log_login_attempt("失敗", "帳號或密碼錯誤")
                            self.log_activity("登入", False, "帳號或密碼錯誤")
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
                    self._log_login_attempt("失敗", "帳號或密碼錯誤")
                    self.log_activity("登入", False, "帳號或密碼錯誤")
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
    
    def logout(self):
        """執行 CMONEY 登出流程 - 關閉事件循環"""
        try:
            print("執行 CMONEY 登出操作")
            
            # 使用保存的事件循環
            if hasattr(self, '_current_loop') and self._current_loop:
                try:
                    result = self._current_loop.run_until_complete(self._logout_async())
                    return result
                finally:
                    # 登出時才關閉事件循環
                    self._current_loop.close()
                    delattr(self, '_current_loop')
            else:
                # 如果沒有保存的循環，創建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self._logout_async())
                    return result
                finally:
                    loop.close()
                    
        except Exception as e:
            print(f"登出過程發生錯誤: {e}")
            self.log_activity("登出", False, f"登出錯誤：{str(e)}")
            self.is_login = False
            return False

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
                    WHERE account_id = %s AND site_name = 'CMONEY' AND logout_time IS NULL
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

    def _log_login_attempt(self, status, message=None):
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
                login_message = f"下次登入時間: {next_login_time}"  # 移除 "CMONEY 登入成功" 字樣
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

    def _calculate_next_login_time(self):
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