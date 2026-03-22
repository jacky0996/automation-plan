#!/bin/bash
set -e
export MYSQL_PWD="$DB_PASSWORD"

echo "等待資料庫啟動..."
until mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" -e "SELECT 1" >/dev/null 2>&1; do
    echo "資料庫尚未準備好，等待中..."
    sleep 2
done

echo "資料庫已啟動，開始執行資料庫重建與初始化腳本..."
# 執行 sql 敘述來重新建立資料庫與新增資料
mysql -h "$DB_HOST" -P "$DB_PORT" -u"$DB_USER" < /app/automation_plan.sql

echo "執行 cmoneyStockScraper.py ..."
python /app/cmoneyStockScraper.py

echo "清理舊的程序鎖檔案 (若存在)..."
rm -f /app/tmp/login_process_lock

echo "啟動主應用程式..."
exec "$@"
