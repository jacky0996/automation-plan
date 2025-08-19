import PyPtt
import mysql.connector
from mysql.connector import Error
from config import HEADLESS_BROWSER, DB_CONFIG
import requests
from bs4 import BeautifulSoup
import time

class PTTHotScraper:
    def __init__(self):
        self.ptt_bot = PyPtt.API()
        self.conn = None
        
    def connect_db(self):
        """連接資料庫"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return True
        except Error as e:
            print(f"資料庫連接失敗: {e}")
            return False
    
    def get_search_configs(self):
        """從資料庫取得搜尋設定"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return []
                    
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT board, keywords, limit_replay_count 
                FROM ptt_get_post_by_board
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            search_configs = []
            for board, keywords, limit_count in results:
                search_configs.append({
                    'board': board,
                    'keywords': keywords,
                    'limit_replay_count': limit_count
                })
            
            print(f"找到 {len(search_configs)} 個搜尋設定")
            return search_configs
            
        except Error as e:
            print(f"查詢搜尋設定時發生錯誤: {e}")
            return []
    
    def get_aid_from_url(self, url):
        """使用 PyPtt API 從 URL 取得 board 和 aid"""
        try:
            board, aid = self.ptt_bot.get_aid_from_url(url)
            return board, aid
        except Exception as e:
            print(f"從 URL 取得 aid 時發生錯誤: {e}")
            return None, None
    
    def save_to_ptt_aid_from_scraper(self, url, board, aid):
        """儲存到 ptt_aid_from_scraper 資料表"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False
            
            cursor = self.conn.cursor()
            
            # 檢查是否已存在相同記錄（避免重複）
            cursor.execute("""
                SELECT id FROM ptt_aid_from_scraper 
                WHERE aid = %s AND board = %s
            """, (aid, board))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"記錄已存在 (aid={aid}, board={board})，跳過插入")
                cursor.close()
                return True
            
            # 插入新記錄
            cursor.execute("""
                INSERT INTO ptt_aid_from_scraper (aid, url, board, created_at) 
                VALUES (%s, %s, %s, NOW())
            """, (aid, url, board))
            
            self.conn.commit()
            cursor.close()
            
            print(f"成功儲存到 ptt_aid_from_scraper: aid={aid}, board={board}, url={url}")
            return True
            
        except Error as e:
            print(f"儲存到資料庫時發生錯誤: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def scrape_hot_posts(self, board, keywords):
        """爬取熱門文章"""
        try:
            # 構建搜尋 URL
            search_url = f"https://www.ptt.cc/bbs/{board}/search?q={keywords}"
            print(f"搜尋 URL: {search_url}")
            
            # 設定 headers 模擬瀏覽器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 發送請求
            response = requests.get(search_url, headers=headers, cookies={'over18': '1'})
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 尋找文章列表
            articles = soup.find_all('div', class_='r-ent')
            
            hot_posts = []
            for article in articles[:10]:  # 只取前10篇
                try:
                    # 取得標題連結
                    title_tag = article.find('a')
                    if not title_tag:
                        continue
                        
                    title = title_tag.text.strip()
                    link = 'https://www.ptt.cc' + title_tag.get('href', '')
                    
                    # 取得推文數
                    push_tag = article.find('div', class_='nrec')
                    push_count = 0
                    if push_tag:
                        push_text = push_tag.text.strip()
                        if push_text.isdigit():
                            push_count = int(push_text)
                        elif push_text == '爆':
                            push_count = 100
                        elif push_text.startswith('X'):
                            try:
                                push_count = -int(push_text[1:])
                            except:
                                push_count = 0
                    
                    # 取得作者
                    author_tag = article.find('div', class_='author')
                    author = author_tag.text.strip() if author_tag else '未知'
                    
                    # 取得日期
                    date_tag = article.find('div', class_='date')
                    date = date_tag.text.strip() if date_tag else '未知'
                    
                    post_info = {
                        'title': title,
                        'link': link,
                        'push_count': push_count,
                        'author': author,
                        'date': date,
                        'board': board,
                        'keywords': keywords
                    }
                    
                    hot_posts.append(post_info)
                    print(f"找到文章: {title} (推文數: {push_count})")
                    
                except Exception as e:
                    print(f"解析文章時發生錯誤: {e}")
                    continue
            
            return hot_posts
            
        except Exception as e:
            print(f"爬取 {board} 板 '{keywords}' 關鍵字時發生錯誤: {e}")
            return []
    
    def run(self):
        """執行熱門文章爬取"""
        try:
            # 取得搜尋設定
            search_configs = self.get_search_configs()
            if not search_configs:
                print("沒有找到搜尋設定")
                return []
            
            all_hot_posts = []
            saved_count = 0
            
            # 迴圈處理每個搜尋設定
            for config in search_configs:
                board = config['board']
                keywords = config['keywords']
                limit_count = config['limit_replay_count']
                
                print(f"\n正在爬取 {board} 板的 '{keywords}' 關鍵字...")
                
                # 爬取熱門文章
                hot_posts = self.scrape_hot_posts(board, keywords)
                
                # 過濾推文數符合條件的文章
                filtered_posts = [
                    post for post in hot_posts 
                    if post['push_count'] >= limit_count
                ]
                
                print(f"在 {board} 板找到 {len(hot_posts)} 篇文章，其中 {len(filtered_posts)} 篇符合推文數條件 (>= {limit_count})")
                
                # 處理符合條件的文章，取得 aid 並儲存到資料庫
                for post in filtered_posts:
                    try:
                        url = post['link']
                        print(f"正在處理文章: {post['title']}")
                        print(f"URL: {url}")
                        
                        # 使用 PyPtt API 從 URL 取得 board 和 aid
                        extracted_board, aid = self.get_aid_from_url(url)
                        
                        if aid and extracted_board:
                            print(f"成功取得 aid: {aid}, board: {extracted_board}")
                            
                            # 儲存到資料庫
                            if self.save_to_ptt_aid_from_scraper(url, extracted_board, aid):
                                saved_count += 1
                                # 將 aid 資訊加入到 post 物件中
                                post['aid'] = aid
                                post['extracted_board'] = extracted_board
                            else:
                                print(f"儲存失敗: {url}")
                        else:
                            print(f"無法從 URL 取得 aid: {url}")
                        
                        # 避免太頻繁呼叫 API
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"處理文章時發生錯誤: {e}")
                        continue
                
                all_hot_posts.extend(filtered_posts)
                
                # 避免請求太頻繁
                time.sleep(1)
            
            print(f"\n總共找到 {len(all_hot_posts)} 篇符合條件的熱門文章")
            print(f"成功儲存 {saved_count} 篇文章到資料庫")
            return all_hot_posts
            
        except Exception as e:
            print(f"執行爬取任務時發生錯誤: {e}")
            return []
        finally:
            # 關閉資料庫連接
            if self.conn:
                self.conn.close()

def main():
    try:
        scraper = PTTHotScraper()
        hot_posts = scraper.run()
        
        # 顯示結果
        if hot_posts:
            print("\n=== 熱門文章列表 ===")
            for i, post in enumerate(hot_posts, 1):
                print(f"{i}. [{post['board']}] {post['title']}")
                print(f"   作者: {post['author']} | 推文數: {post['push_count']} | 日期: {post['date']}")
                print(f"   連結: {post['link']}")
                print(f"   搜尋關鍵字: {post['keywords']}")
                
                # 顯示 aid 資訊（如果有的話）
                if 'aid' in post and 'extracted_board' in post:
                    print(f"   AID: {post['aid']} | 提取的板名: {post['extracted_board']}")
                    print(f"   ✓ 已儲存到資料庫")
                else:
                    print(f"   ✗ 未能取得 AID 或未儲存到資料庫")
                
                print("-" * 50)
        else:
            print("沒有找到符合條件的熱門文章")
            
    except Exception as e:
        print(f"\n程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()