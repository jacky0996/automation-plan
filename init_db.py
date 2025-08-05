"""
資料庫初始化腳本
創建 users 表來支援 API 認證
"""

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from api.auth import get_password_hash

def create_users_table():
    """創建 users 表"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 創建 users 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        print("users 表創建成功或已存在")
        
        # 檢查是否有預設管理員帳號
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # 創建預設管理員帳號
            admin_password_hash = get_password_hash("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, is_admin)
                VALUES (%s, %s, %s, %s)
            """, ("admin", admin_password_hash, "admin@example.com", True))
            print("預設管理員帳號已創建 (username: admin, password: admin123)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"創建 users 表失敗: {e}")
        return False

def init_database():
    """初始化資料庫"""
    print("開始初始化資料庫...")
    
    success = create_users_table()
    
    if success:
        print("資料庫初始化完成")
    else:
        print("資料庫初始化失敗")
    
    return success

if __name__ == "__main__":
    init_database()
