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

# FastAPI 設定
API_CONFIG = {
    'host': os.getenv('API_HOST', '0.0.0.0'),
    'port': int(os.getenv('API_PORT', '8000')),
    'reload': os.getenv('API_RELOAD', 'False').lower() in ('true', '1', 't'),
    'log_level': os.getenv('API_LOG_LEVEL', 'info')
}

# JWT 設定
JWT_CONFIG = {
    'secret_key': os.getenv('JWT_SECRET_KEY', 'your-secret-key-here-change-in-production'),
    'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
    'access_token_expire_minutes': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
}

# 瀏覽器設定
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'True').lower() in ('true', '1', 't')

# 其他一般設定
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# CORS 設定
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# 任務設定
TASK_CONFIG = {
    'default_delay_min': int(os.getenv('TASK_DELAY_MIN', '5')),
    'default_delay_max': int(os.getenv('TASK_DELAY_MAX', '15')),
    'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', '5'))
}