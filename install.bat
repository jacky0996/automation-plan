@echo off
echo 正在安裝自動登入和發文管理系統...
echo.

echo 檢查 Python 環境...
python --version
if %errorlevel% neq 0 (
    echo 錯誤: 未找到 Python，請先安裝 Python 3.8 或以上版本
    pause
    exit /b 1
)
echo.

echo 安裝 Python 依賴套件...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 錯誤: 安裝依賴套件失敗
    pause
    exit /b 1
)
echo.

echo 檢查環境設定檔...
if not exist .env (
    echo 正在創建 .env 檔案...
    copy .env.example .env
    echo 請編輯 .env 檔案設定資料庫連接資訊
    echo.
)

echo 初始化資料庫...
python init_db.py
if %errorlevel% neq 0 (
    echo 警告: 資料庫初始化失敗，請檢查資料庫連接設定
)
echo.

echo 安裝完成！
echo.
echo 使用方式：
echo 1. API 服務模式：python run.py --mode api
echo 2. 批次處理模式：python run.py --mode batch  
echo 3. 單一帳號模式：python run.py --mode single --site PTT --account 帳號 --password 密碼
echo.
echo API 文件位置：http://localhost:8000/docs
echo.
pause
