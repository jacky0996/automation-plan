"""
FastAPI 主應用程式
自動登入和發文管理系統
"""

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys
from datetime import datetime
from typing import List, Optional

# 導入自定義模組
from api.auth import get_current_user, create_access_token
from api.models import UserResponse, LoginRequest, AccountResponse, TaskResponse
from api.routes import accounts, tasks, logs, auth
from config import DB_CONFIG, API_CONFIG, CORS_ORIGINS

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="自動登入和發文管理系統",
    description="提供 PTT 和 CMoney 自動登入、發文功能的 API 服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認證"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["帳號管理"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["任務管理"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["日誌查詢"])

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "自動登入和發文管理系統 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 簡單的資料庫連接測試
        import mysql.connector
        conn = mysql.connector.connect(**DB_CONFIG)
        conn.close()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/info")
async def api_info():
    """API 資訊"""
    return {
        "name": "自動登入和發文管理系統",
        "version": "1.0.0",
        "description": "提供 PTT 和 CMoney 自動登入、發文功能的 API 服務",
        "endpoints": {
            "認證": "/api/v1/auth",
            "帳號管理": "/api/v1/accounts",
            "任務管理": "/api/v1/tasks",
            "日誌查詢": "/api/v1/logs"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    logger.info("=" * 50)
    logger.info("FastAPI 應用程式啟動")
    logger.info("自動登入和發文管理系統 API 服務已啟動")
    logger.info(f"API 主機: {API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info(f"文件位置: http://{API_CONFIG['host']}:{API_CONFIG['port']}/docs")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    logger.info("FastAPI 應用程式關閉")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        reload=API_CONFIG['reload'],
        log_level=API_CONFIG['log_level']
    )
