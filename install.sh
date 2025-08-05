#!/bin/bash

echo "正在安裝自動登入和發文管理系統..."
echo

echo "檢查 Python 環境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "錯誤: 未找到 Python，請先安裝 Python 3.8 或以上版本"
    exit 1
fi
echo

echo "安裝 Python 依賴套件..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "錯誤: 安裝依賴套件失敗"
    exit 1
fi
echo

echo "檢查環境設定檔..."
if [ ! -f .env ]; then
    echo "正在創建 .env 檔案..."
    cp .env.example .env
    echo "請編輯 .env 檔案設定資料庫連接資訊"
    echo
fi

echo "初始化資料庫..."
python3 init_db.py
if [ $? -ne 0 ]; then
    echo "警告: 資料庫初始化失敗，請檢查資料庫連接設定"
fi
echo

echo "安裝完成！"
echo
echo "使用方式："
echo "1. API 服務模式：python3 run.py --mode api"
echo "2. 批次處理模式：python3 run.py --mode batch"
echo "3. 單一帳號模式：python3 run.py --mode single --site PTT --account 帳號 --password 密碼"
echo
echo "API 文件位置：http://localhost:8000/docs"
echo
