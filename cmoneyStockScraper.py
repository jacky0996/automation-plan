import time
import re
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from cmoneyBase import CMoneyBase
from config import HEADLESS_BROWSER  # 添加引入

class CMoneyStockScraper(CMoneyBase):
    """CMoney 股票爬蟲 - 抓取熱門股票資訊"""
    
    def __init__(self):
        self.url = 'https://www.cmoney.tw/forum/popular/stock'
        self.target_count = 100  # 目標抓取100支股票
        
    def extract_stock_info(self, title):
        """從標題中提取股票代碼和名稱"""
        # 匹配格式: 數字(4位) 空格 中文
        pattern = r'^(\d{4})\s+(.+)$'
        match = re.match(pattern, title.strip())
        
        if match:
            stock_code = match.group(1)
            stock_name = match.group(2).strip()
            
            # 排除ETF等非個股
            etf_keywords = ['ETF', 'etf', '指數', '基金', '期貨', '選擇權']
            for keyword in etf_keywords:
                if keyword in stock_name:
                    return None
            
            return stock_code, stock_name
        
        return None
    
    def get_next_weekend(self):
        """取得下一個週末的日期"""
        today = datetime.now().date()
        days_ahead = 6 - today.weekday()  # 6 = 週日
        if days_ahead <= 0:  # 今天是週日或之後
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def scrape_stocks_with_scroll(self):
        """使用 Playwright 抓取股票，支援滾動載入更多內容"""
        stocks = []
        processed_titles = set()  # 避免重複處理同一個標題
        
        try:
            with sync_playwright() as p:
                print("啟動瀏覽器...")
                browser = p.chromium.launch(headless=HEADLESS_BROWSER)  # 設為 True 可背景執行
                context = browser.new_context()
                page = context.new_page()
                
                print(f"前往頁面: {self.url}")
                page.goto(self.url)
                
                # 等待頁面載入
                time.sleep(3)
                scroll_attempts = 0
                max_scrolls = 20  # 最多滾動20次

                while len(stocks) < self.target_count and scroll_attempts < max_scrolls:
                    print(f"第 {scroll_attempts + 1} 次滾動，目前找到 {len(stocks)} 支股票")
                    
                    # 找到所有 class='headline__title' 元素
                    title_elements = page.query_selector_all('.headline__title')
                    print(f"頁面上共找到 {len(title_elements)} 個 headline__title 元素")
                    
                    # 處理每個標題元素
                    for element in title_elements:
                        # try:
                            # 直接取得這個 h3 元素的 title 屬性值
                            title = element.get_attribute('title')
                            
                            if not title:
                                print("該元素沒有 title 屬性，跳過")
                                continue
                            
                            title = title.strip()
                            print(f"取得 title 屬性值: {title}")
                            
                            # 跳過已處理過的標題
                            if title in processed_titles:
                                continue
                            
                            processed_titles.add(title)
                            
                            # 提取股票資訊
                            stock_info = self.extract_stock_info(title)
                            
                            if stock_info:
                                stock_code, stock_name = stock_info
                                
                                # 檢查是否已經在股票列表中（避免重複）
                                if not any(s[0] == stock_code for s in stocks):
                                    stocks.append((stock_code, stock_name))
                                    print(f"✓ 找到符合格式的股票: {stock_code} {stock_name}")
                                    
                                    # 達到目標數量就跳出 for 迴圈
                                    if len(stocks) >= self.target_count:
                                        print(f"已達到目標數量 {self.target_count} 支股票")
                                        break
                            else:
                                print(f"✗ 不符合股票格式，排除: {title}")
                                
                        # except Exception as e:
                        #     print(f"處理標題時出錯: {e}")
                        #     continue

                    # 如果已達目標數量，停止滾動
                    if len(stocks) >= self.target_count:
                        break

                    # 改用分段滾動策略
                    print("開始細緻滾動...")

                    # 取得當前頁面信息
                    viewport_height = page.evaluate("window.innerHeight")
                    current_scroll = page.evaluate("window.pageYOffset") 
                    total_height = page.evaluate("document.body.scrollHeight")

                    print(f"視窗高度: {viewport_height}, 當前位置: {current_scroll}, 總高度: {total_height}")

                    # 每次滾動一個視窗高度
                    next_scroll = current_scroll + viewport_height
                    if next_scroll > total_height - viewport_height:
                        next_scroll = total_height - viewport_height

                    print(f"滾動到位置: {next_scroll}")
                    page.evaluate(f"window.scrollTo({{top: {next_scroll}, behavior: 'smooth'}})")

                    # 等待滾動和內容載入
                    time.sleep(2)

                    # 檢查是否有新內容載入
                    new_total_height = page.evaluate("document.body.scrollHeight")
                    if new_total_height > total_height:
                        print(f"發現新內容！頁面高度增加: {total_height} -> {new_total_height}")
                    else:
                        print("沒有新內容載入")

                    scroll_attempts += 1

            browser.close()
            
        except Exception as e:
            print(f"抓取股票時發生錯誤: {e}")
    
        print(f"抓取完成，共找到 {len(stocks)} 支符合格式的股票")
        return stocks[:self.target_count]  # 只取前100支
    
    def update_database(self, stocks):
        """更新資料庫"""
        try:
            # 每次都重新連接資料庫
            conn = self._connect_db()
            if not conn:
                print("無法連接資料庫")
                return False
            
            cursor = conn.cursor()
            next_weekend = self.get_next_weekend()
            
            updated_count = 0
            inserted_count = 0
            
            for stock_code, stock_name in stocks:
                # 檢查是否已存在
                cursor.execute("""
                    SELECT id FROM cmoney_get_board_by_popular 
                    WHERE code = %s
                """, (stock_code,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 更新最後使用時間
                    cursor.execute("""
                        UPDATE cmoney_get_board_by_popular 
                        SET name = %s, last_use_time = %s 
                        WHERE code = %s
                    """, (stock_name, next_weekend, stock_code))
                    updated_count += 1
                    print(f"更新股票: {stock_code} {stock_name}")
                else:
                    # 插入新記錄
                    cursor.execute("""
                        INSERT INTO cmoney_get_board_by_popular (code, name, last_use_time) 
                        VALUES (%s, %s, %s)
                    """, (stock_code, stock_name, next_weekend))
                    inserted_count += 1
                    print(f"新增股票: {stock_code} {stock_name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"資料庫更新完成 - 新增: {inserted_count}, 更新: {updated_count}")
            return True
            
        except Exception as e:
            print(f"資料庫更新失敗: {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False
    
    def run(self):
        """主執行函數"""
        print("=== CMoney 股票爬蟲開始執行 ===")
        
        try:
            # 抓取股票資料
            print("開始抓取股票資料...")
            stocks = self.scrape_stocks_with_scroll()
            
            if stocks:
                print(f"成功抓取 {len(stocks)} 支股票，開始更新資料庫...")
                success = self.update_database(stocks)
                
                if success:
                    print("✓ 資料庫更新成功")
                    return True
                else:
                    print("✗ 資料庫更新失敗")
                    return False
            else:
                print("未抓取到任何股票資料")
                return False
                
        except Exception as e:
            print(f"執行過程中發生錯誤: {e}")
            return False

    def _connect_db(self):
        """連接資料庫"""
        try:
            from config import DB_CONFIG
            import mysql.connector
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return self.conn
        except Exception as e:
            print(f"資料庫連接失敗: {e}")
            return None

def main():
    """主程式入口"""
    try:
        scraper = CMoneyStockScraper()
        result = scraper.run()
        
        if result:
            print("\n✓ CMoney 股票爬蟲執行成功")
        else:
            print("\n✗ CMoney 股票爬蟲執行失敗")
            
    except KeyboardInterrupt:
        print("\n程式被使用者中斷")
    except Exception as e:
        print(f"\n程式執行錯誤: {e}")

if __name__ == "__main__":
    main()