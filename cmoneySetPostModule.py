import random
from cmoneyBase import CMoneyBase

class CMoneySetPostBot(CMoneyBase):
    """專門處理 CMONEY 文章準備功能的類別"""
    
    def __init__(self, account, password):
        super().__init__(account, password)
    
    def prepare_articles(self):
        """準備文章任務 - 從股票和模板數據創建文章"""
        try:
            print("開始準備文章任務...")
            
            # 連接資料庫
            conn = self._connect_db()
            if not conn:
                print("無法連接資料庫")
                return False
            
            cursor = conn.cursor()
            
            # 1. 隨機選擇股票
            cursor.execute("""
                SELECT code, name 
                FROM cmoney_get_board_by_popular 
                ORDER BY RAND() 
                LIMIT 1
            """)
            
            stock_result = cursor.fetchone()
            if not stock_result:
                print("沒有找到可用的股票資料")
                cursor.close()
                conn.close()
                return False
            
            stock_code, stock_name = stock_result
            print(f"選擇股票: {stock_code} {stock_name}")
            
            # 2. 隨機選擇內容模板
            cursor.execute("""
                SELECT content 
                FROM replay_template 
                WHERE site = 'CMONEY'
                ORDER BY RAND() 
                LIMIT 1
            """)
            
            template_result = cursor.fetchone()
            if not template_result:
                print("沒有找到可用的 CMONEY 內容模板")
                cursor.close()
                conn.close()
                return False
            
            content = template_result[0]
            print(f"選擇內容模板: {content[:50]}...")
            
            # 3. 插入新文章任務
            cursor.execute("""
                INSERT INTO posts (
                    account_id, board, title, content, platform, category
                ) VALUES (
                    %s, %s, %s, %s, 'cmoney', 'post'
                )
            """, (self.account_id, stock_code, stock_name, content))
            
            conn.commit()
            post_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            print(f"成功創建文章任務 ID: {post_id}")
            print(f"看板: {stock_code}, 標題: {stock_name}")
            print(f"內容: {content[:100]}...")
            
            # 記錄活動日誌
            self.log_activity("文章準備", True, f"成功創建文章任務 ID: {post_id}, 股票: {stock_code} {stock_name}")
            
            return True
            
        except Exception as e:
            print(f"準備文章任務時發生錯誤: {e}")
            self.log_activity("文章準備", False, f"錯誤: {str(e)}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False
    
    def prepare_multiple_articles(self, count=1):
        """準備多篇文章任務"""
        try:
            success_count = 0
            
            for i in range(count):
                print(f"準備第 {i+1}/{count} 篇文章...")
                if self.prepare_articles():
                    success_count += 1
                else:
                    print(f"第 {i+1} 篇文章準備失敗")
            
            print(f"文章準備完成，成功: {success_count}/{count}")
            return success_count > 0
            
        except Exception as e:
            print(f"準備多篇文章時發生錯誤: {e}")
            return False
    
    def get_stock_count(self):
        """取得可用股票數量"""
        try:
            conn = self._connect_db()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cmoney_get_board_by_popular")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"取得股票數量時發生錯誤: {e}")
            return 0
    
    def get_template_count(self):
        """取得可用模板數量"""
        try:
            conn = self._connect_db()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM replay_template WHERE site = 'CMONEY'")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"取得模板數量時發生錯誤: {e}")
            return 0
    
    def check_resources(self):
        """檢查資源是否充足"""
        try:
            stock_count = self.get_stock_count()
            template_count = self.get_template_count()
            
            print(f"可用股票數量: {stock_count}")
            print(f"可用模板數量: {template_count}")
            
            if stock_count == 0:
                print("警告：沒有可用的股票資料")
                return False
            
            if template_count == 0:
                print("警告：沒有可用的 CMONEY 模板")
                return False
            
            print("資源檢查通過")
            return True
            
        except Exception as e:
            print(f"檢查資源時發生錯誤: {e}")
            return False
    
    def check_posted_today(self):
        """檢查當前帳號今日是否已發文"""
        try:
            conn = self._connect_db()
            if not conn:
                print("無法連接資料庫，預設為未發文")
                return False
            
            cursor = conn.cursor()
            
            # 查詢今日是否有成功發文記錄
            cursor.execute("""
                SELECT COUNT(*) 
                FROM posts 
                WHERE account_id = %s 
                AND platform = 'cmoney' 
                AND result = 'success'
                AND DATE(post_time) = CURDATE()
            """, (self.account_id,))
            
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            if count > 0:
                print(f"今日已發文 {count} 篇")
                return True
            else:
                print("今日尚未發文")
                return False
            
        except Exception as e:
            print(f"檢查今日發文狀態時發生錯誤: {e}")
            return False  # 出錯時預設為未發文，允許執行準備任務