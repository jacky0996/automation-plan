"""
簡單的 FastAPI 測試服務
用於驗證基本功能
"""

from fastapi import FastAPI
import uvicorn
from datetime import datetime

# 創建 FastAPI 應用
app = FastAPI(
    title="自動登入和發文管理系統",
    description="測試版本",
    version="1.0.0"
)

@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "自動登入和發文管理系統 API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("啟動 FastAPI 測試服務...")
    print("服務位置: http://localhost:8000")
    print("API 文件: http://localhost:8000/docs")
    uvicorn.run(
        "test_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
