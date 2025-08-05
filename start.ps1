# PowerShell 啟動腳本

Write-Host "自動登入和發文管理系統 - FastAPI 版本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 檢查虛擬環境
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "✓ 找到虛擬環境" -ForegroundColor Green
    $python = ".\.venv\Scripts\python.exe"
} else {
    Write-Host "✗ 未找到虛擬環境，使用系統 Python" -ForegroundColor Yellow
    $python = "python"
}

Write-Host ""
Write-Host "可用的執行選項：" -ForegroundColor Cyan
Write-Host "1. 啟動 API 服務 (推薦)"
Write-Host "2. 執行批次處理"
Write-Host "3. 測試單一帳號"
Write-Host "4. 初始化資料庫"
Write-Host "5. 啟動簡化測試服務"
Write-Host ""

$choice = Read-Host "請選擇執行選項 (1-5)"

switch ($choice) {
    "1" {
        Write-Host "啟動 API 服務..." -ForegroundColor Green
        Write-Host "服務位置: http://localhost:8000" -ForegroundColor Yellow
        Write-Host "API 文件: http://localhost:8000/docs" -ForegroundColor Yellow
        Write-Host "按 Ctrl+C 停止服務" -ForegroundColor Red
        & $python run.py --mode api
    }
    "2" {
        Write-Host "執行批次處理..." -ForegroundColor Green
        & $python run.py --mode batch
    }
    "3" {
        $site = Read-Host "請輸入網站類型 (PTT 或 CMONEY)"
        $account = Read-Host "請輸入帳號"
        $password = Read-Host "請輸入密碼" -AsSecureString
        $passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
        & $python run.py --mode single --site $site --account $account --password $passwordPlain
    }
    "4" {
        Write-Host "初始化資料庫..." -ForegroundColor Green
        & $python init_db.py
    }
    "5" {
        Write-Host "啟動簡化測試服務..." -ForegroundColor Green
        Write-Host "服務位置: http://localhost:8000" -ForegroundColor Yellow
        Write-Host "按 Ctrl+C 停止服務" -ForegroundColor Red
        & $python test_app.py
    }
    default {
        Write-Host "無效的選項，正在啟動 API 服務..." -ForegroundColor Yellow
        & $python run.py --mode api
    }
}

Write-Host ""
Write-Host "程式執行完畢" -ForegroundColor Green
Read-Host "按 Enter 鍵退出"
