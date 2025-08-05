"""
FastAPI 應用的啟動腳本
替代原本的 main.py，支援 API 模式和原始批次模式
"""

import sys
import argparse
import logging
from datetime import datetime

# 設置日誌系統
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_plan.log', encoding='utf-8', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_api_server():
    """啟動 FastAPI 服務器"""
    import uvicorn
    logger.info("啟動 FastAPI 服務器...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生產環境中應該設為 False
        log_level="info"
    )

def run_batch_mode():
    """執行原始的批次處理模式"""
    logger.info("執行批次處理模式...")
    
    from services.login_service import LoginService
    
    login_service = LoginService()
    
    # 獲取需要登入的帳號
    accounts = login_service.get_accounts_due_for_login()
    
    if not accounts:
        logger.info("本次執行沒有需要登入的帳號，程式結束")
        return
    
    # 處理所有帳號
    results = login_service.process_multiple_accounts(accounts)
    
    logger.info("=" * 50)
    logger.info("批次處理完成")
    logger.info(f"總計處理: {results['total']} 個帳號")
    logger.info(f"成功: {results['successful']} 個")
    logger.info(f"失敗: {results['failed']} 個")
    logger.info("=" * 50)

def run_single_account(site_type: str, account: str, password: str):
    """執行單一帳號登入"""
    logger.info(f"執行單一帳號登入: {site_type} - {account}")
    
    from services.login_service import LoginService
    
    login_service = LoginService()
    success = login_service.process_single_account(site_type, account, password)
    
    if success:
        logger.info(f"帳號 {account} 登入成功")
    else:
        logger.error(f"帳號 {account} 登入失敗")
    
    return success

def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(description="自動登入和發文管理系統")
    parser.add_argument(
        "--mode", 
        choices=["api", "batch", "single"], 
        default="api",
        help="執行模式: api(API服務器), batch(批次處理), single(單一帳號)"
    )
    parser.add_argument("--site", help="網站類型 (PTT 或 CMONEY)，用於 single 模式")
    parser.add_argument("--account", help="帳號名稱，用於 single 模式")
    parser.add_argument("--password", help="密碼，用於 single 模式")
    
    args = parser.parse_args()
    
    logger.info("=" * 50)
    logger.info("自動登入和發文管理系統")
    logger.info(f"啟動時間: {datetime.now()}")
    logger.info(f"執行模式: {args.mode}")
    logger.info("=" * 50)
    
    try:
        if args.mode == "api":
            run_api_server()
        elif args.mode == "batch":
            run_batch_mode()
        elif args.mode == "single":
            if not all([args.site, args.account, args.password]):
                logger.error("single 模式需要提供 --site, --account, --password 參數")
                sys.exit(1)
            run_single_account(args.site, args.account, args.password)
        
    except KeyboardInterrupt:
        logger.info("程式被使用者中斷")
    except Exception as e:
        logger.error(f"程式執行錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
