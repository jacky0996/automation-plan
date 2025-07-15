import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 資料庫設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'automation_plan')
}

# 其他一般設定
# DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
# LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'True').lower() in ('true', '1', 't')