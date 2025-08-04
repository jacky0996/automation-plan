import time
import random
import asyncio
from cmoneyLoginModule import CMoneyLoginBot
from cmoneyPostModule import CMoneyPostBot
from cmoneySetPostModule import CMoneySetPostBot  # 引入文章準備模組

class CMoneyBot(CMoneyLoginBot, CMoneyPostBot, CMoneySetPostBot):  # 繼承文章準備模組
    """整合所有 CMONEY 功能的主類"""
    
    def __init__(self, account, password):
        # 先初始化 LoginBot（包含瀏覽器屬性）
        CMoneyLoginBot.__init__(self, account, password)
        # 然後初始化 PostBot，但不覆蓋瀏覽器屬性
        # 只初始化 PostBot 特有的屬性
        self.posts_processed = 0
        # SetPostBot 使用相同的基類屬性，不需要額外初始化
    
    def login_and_perform_tasks(self):
        """登入並執行所有任務 - 在同一個異步方法中完成"""
        try:
            print("開始執行 CMONEY 登入與發文任務")
            
            # 使用一個統一的異步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self._unified_login_and_post())
                return result
            finally:
                loop.close()
                
        except Exception as e:
            print(f"執行任務時發生錯誤: {e}")
            return False
    
    async def _unified_login_and_post(self):
        """統一的異步登入和發文方法"""
        try:
            # 初始化瀏覽器
            if not await self._init_browser():
                print("瀏覽器初始化失敗")
                return False
            
            # 執行登入
            login_success = await self._login_async()
            if not login_success:
                print("登入失敗")
                await self._close_browser()
                return False
            
            print("登入成功，檢查今日是否已發文")
            
            # 檢查今日是否已發文
            has_posted_today = self.check_posted_today()
            
            if has_posted_today:
                print("今日已發過文，跳過文章準備任務")
            else:
                print("今日尚未發文，準備執行文章準備任務")
                # 新增：準備文章任務（使用 cmoneySetPostModule 的功能）
                article_prepared = self.prepare_articles()  # 這個方法來自 CMoneySetPostBot
                if not article_prepared:
                    print("文章準備失敗，但繼續執行發文任務")
            
            print("準備執行發文任務")
            
            # 直接執行發文任務（在同一個事件循環中）
            posts_result = await self._process_forum_posts()
            
            if posts_result == -1:
                print("發文模組要求登出")
                await self._logout_async()
                await self._close_browser()
                return False
            
            print(f"發文任務完成，處理了 {posts_result} 篇文章")
            
            # 登出
            await self._logout_async()
            await self._close_browser()
            
            return True
            
        except Exception as e:
            print(f"統一執行過程中發生錯誤: {e}")
            try:
                await self._close_browser()
            except:
                pass
            return False

    def verify_browser_instance(self):
        """驗證瀏覽器實例是否有效"""
        try:
            if not self.page:
                print("錯誤：瀏覽器頁面實例為空")
                return False
            
            if not self.browser:
                print("錯誤：瀏覽器實例為空")
                return False
            
            # 檢查頁面是否可訪問
            current_url = self.page.url
            print(f"瀏覽器實例驗證成功，當前頁面: {current_url}")
            
            # 檢查是否已登入 CMoney
            if "cmoney.tw" in current_url:
                print("已在 CMoney 網站，瀏覽器實例有效")
                return True
            else:
                print(f"警告：當前不在 CMoney 網站 (URL: {current_url})")
                return True  # 仍然返回 True，因為可能需要跳轉
                
        except Exception as e:
            print(f"驗證瀏覽器實例時出錯: {e}")
            return False

def process_login(account, password):
    """CMONEY 登入處理函數 - 被 main.py 調用"""
    try:
        print(f"開始處理 CMONEY 帳號: {account}")
        
        # 創建整合的 CMONEY 機器人
        bot = CMoneyBot(account, password)
        
        # 執行登入和所有任務（包含文章準備）
        success = bot.login_and_perform_tasks()
        
        if success:
            print(f"CMONEY 帳號 {account} 處理完成")
        else:
            print(f"CMONEY 帳號 {account} 處理失敗")
            
        return success
        
    except Exception as e:
        print(f"處理 CMONEY 帳號 {account} 時發生錯誤: {e}")
        return False

if __name__ == "__main__":
    # 測試用
    import sys
    if len(sys.argv) >= 3:
        account = sys.argv[1]
        password = sys.argv[2]
        process_login(account, password)
    else:
        print("請提供帳號和密碼")