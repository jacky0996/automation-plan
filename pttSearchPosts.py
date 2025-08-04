import time
import sys
import random
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import PyPtt

class PttSearchBot:
    """PTT 關鍵字搜尋機器人"""
    
    def __init__(self):
        self.ptt_bot = None
        self.account = None
        self.password = None
        self.account_id = None
        self.conn = None
        
    def connect_db(self):
        """連接資料庫"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            return True
        except Error as e:
            print(f"資料庫連接失敗: {e}")
            return False
    
    def get_first_ptt_account(self):
        """取得第一個 status=1 且 account_type='PTT' 的帳號"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False
                    
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, account, password 
                FROM accounts 
                WHERE status = 1 AND account_type = 'PTT' 
                ORDER BY id ASC 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                self.account_id, self.account, self.password = result
                print(f"找到可用帳號: {self.account} (ID: {self.account_id})")
                return True
            else:
                print("未找到可用的 PTT 帳號")
                return False
                
        except Error as e:
            print(f"查詢帳號時發生錯誤: {e}")
            return False
    
    def get_search_boards(self):
        """取得要搜尋的看板和關鍵字列表"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return []
                    
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT borad, keywords, limit_replay_count 
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
    
    def login(self):
        """登入 PTT"""
        try:
            print(f"準備登入 PTT 帳號: {self.account}")
            
            self.ptt_bot = PyPtt.API()
            self.ptt_bot.login(
                self.account, 
                self.password,
            )
            
            print(f"帳號 {self.account} 登入成功")
            return True
            
        except Exception as e:
            print(f"登入失敗: {e}")
            return False
    
    def logout(self):
        """登出 PTT"""
        try:
            self.ptt_bot.logout()
            print(f"帳號 {self.account} 已登出")
        except Exception as e:
            print(f"登出時發生錯誤: {e}")
    
    def search_posts_by_keyword(self, board, keywords, limit_replay_count=0):
        """在指定看板搜尋關鍵字"""
        try:
            print(f"在看板 {board} 搜尋關鍵字: {keywords}")
            
            # 搜尋文章
            search_list = self.ptt_bot.get_post(
                board,
                index=1,
                search_list=[(PyPtt.SearchType.KEYWORD, keywords)]
            )
            
            found_posts = []
            
            if search_list:
                # 檢查文章是否被鎖定
                if search_list.get('is_lock') != True:  # 文章未被鎖定
                    print("文章未被鎖定，可以處理")
                    
                    # 取得推文數並轉換類型
                    push_count_raw = search_list.get('push_number', 0)
                    
                    # 處理推文數的類型轉換
                    try:
                        if isinstance(push_count_raw, str):
                            # 如果是字串，嘗試轉換為整數
                            if push_count_raw.isdigit():
                                push_count = int(push_count_raw)
                            elif push_count_raw == '爆':  # PTT 的爆文標示
                                push_count = 100  # 爆文視為100推
                            elif push_count_raw.startswith('X'):  # 負推文 (如 X1, X2)
                                push_count = -int(push_count_raw[1:]) if push_count_raw[1:].isdigit() else 0
                            else:
                                push_count = 0
                        elif isinstance(push_count_raw, int):
                            push_count = push_count_raw
                        else:
                            push_count = 0
                            
                        print(f"推文數 (轉換後): {push_count}")
                        
                    except (ValueError, IndexError) as convert_error:
                        print(f"推文數轉換失敗: {convert_error}, 使用預設值 0")
                        push_count = 0
                    
                    # 確保 limit_replay_count 也是整數
                    try:
                        limit_count = int(limit_replay_count)
                    except (ValueError, TypeError):
                        limit_count = 0
                        print(f"最低推文數轉換失敗，使用預設值 0")
                    
                    # 檢查推文數是否符合條件
                    if push_count >= limit_count:
                        print(f"推文數 {push_count} 符合最低要求 {limit_count}")
                        
                        # 取得隨機推文模板
                        content_id = self.get_random_reply_template(board)
                        
                        if content_id:
                            # 儲存到資料庫
                            success = self.save_to_ptt_push_post(
                                board=board,
                                aid=search_list.get('aid'),
                                content_id=content_id
                            )
                            
                            if success:
                                found_posts.append({
                                    'board': board,
                                    'aid': search_list.get('aid'),
                                    'title': search_list.get('title', ''),
                                    'push_count': push_count,
                                    'content_id': content_id,
                                    'search_keyword': keywords
                            })
                                print("✓ 已成功儲存到資料庫")
                            else:
                                print("✗ 儲存到資料庫失敗")
                        else:
                            print("✗ 未找到可用的推文模板")
                    else:
                        print(f"推文數 {push_count} 不符合最低要求 {limit_count}")
                else:
                    print("文章已被鎖定，跳過處理")
            else:
                print(f"在看板 {board} 中沒有找到關鍵字 '{keywords}' 的相關文章")
            
            return found_posts
            
        except Exception as e:
            print(f"搜尋文章時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_random_reply_template(self, board):
        """從 replay_template 表中隨機取得一個推文模板ID"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return None
            
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
                content_id = result[0]
                print(f"隨機選擇推文模板ID: {content_id}")
                return content_id
            else:
                print(f"在 replay_template 表中未找到符合條件的模板 (site='PTT', board='{board}')")
                return None
                
        except Error as e:
            print(f"查詢推文模板時發生錯誤: {e}")
            return None

    def save_to_ptt_push_post(self, board, aid, content_id):
        """將搜尋結果儲存到 ptt_push_post 表"""
        try:
            if not self.conn:
                if not self.connect_db():
                    return False
            
            cursor = self.conn.cursor()
            
            # 檢查是否已存在相同記錄（避免重複）
            cursor.execute("""
                SELECT id FROM ptt_push_post 
                WHERE board = %s AND aid = %s
            """, (board, aid))
            
            existing = cursor.fetchone()
            
            if existing:
                print(f"記錄已存在 (board={board}, aid={aid})，跳過插入")
                cursor.close()
                return True
            
            # 插入新記錄
            cursor.execute("""
                INSERT INTO ptt_push_post (board, aid, content_id) 
                VALUES (%s, %s, %s)
            """, (board, aid, content_id))
            
            self.conn.commit()
            cursor.close()
            
            print(f"成功儲存到 ptt_push_post: board={board}, aid={aid}, content_id={content_id}")
            return True
            
        except Error as e:
            print(f"儲存到資料庫時發生錯誤: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def run_search_tasks(self):
        """執行搜尋任務"""
        try:
            # 取得帳號
            if not self.get_first_ptt_account():
                return False
            
            # 取得搜尋設定
            search_configs = self.get_search_boards()
            if not search_configs:
                print("沒有找到搜尋設定")
                return False
            
            # 登入
            if not self.login():
                return False
            
            # 只執行第一個搜尋設定來測試
            if search_configs:
                config = search_configs[0]  # 只取第一個
                board = config['board']
                keywords = config['keywords']
                limit_count = config['limit_replay_count']
                
                print(f"\n開始測試搜尋 - 看板: {board}, 關鍵字: {keywords}, 最低推文數: {limit_count}")
                
                found_posts = self.search_posts_by_keyword(board, keywords, limit_count)
                
                print(f"\n測試完成，找到 {len(found_posts)} 篇文章")
            
            return True
            
        except Exception as e:
            print(f"執行搜尋任務時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 登出
            self.logout()
            
            # 關閉資料庫連接
            if self.conn:
                self.conn.close()

def main():
    """主程式"""
    print("=== PTT 關鍵字搜尋程式 ===")
    
    search_bot = PttSearchBot()
    
    try:
        result = search_bot.run_search_tasks()
        if result:
            print("\n搜尋任務完成")
        else:
            print("\n搜尋任務失敗")
    except KeyboardInterrupt:
        print("\n程式被中斷")
        search_bot.logout()
    except Exception as e:
        print(f"\n程式執行時發生錯誤: {e}")
        search_bot.logout()

if __name__ == "__main__":
    main()