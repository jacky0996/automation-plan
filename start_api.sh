#!/bin/bash
echo "啟動自動登入和發文管理系統 API 服務..."
echo
echo "API 文件位置：http://localhost:8000/docs"
echo "按 Ctrl+C 停止服務"
echo
python3 run.py --mode api
