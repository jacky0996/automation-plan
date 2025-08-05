# 快速入門指南

## 🚀 專案已轉換為 FastAPI！

您的專案已成功轉換為 FastAPI 架構，現在提供以下功能：

### ✨ 新功能
- 🌐 **Web API 介面** - RESTful API 服務
- 📱 **互動式文件** - Swagger UI 和 ReDoc
- 🔐 **認證系統** - JWT Token 認證
- 📊 **任務管理** - 異步任務執行
- 📈 **即時監控** - 任務狀態追蹤
- 🗃️ **日誌查詢** - 完整的登入記錄

### 🎯 執行方式

#### 方法 1: 使用 PowerShell 腳本 (推薦)
```powershell
# 在 PowerShell 中執行
.\start.ps1
```
然後選擇您要的執行模式。

#### 方法 2: 直接命令列執行
```powershell
# 啟動 API 服務
.\.venv\Scripts\python.exe run.py --mode api

# 批次處理模式 (原有功能)
.\.venv\Scripts\python.exe run.py --mode batch

# 單一帳號測試
.\.venv\Scripts\python.exe run.py --mode single --site PTT --account 您的帳號 --password 您的密碼
```

#### 方法 3: 測試服務
```powershell
# 啟動簡化測試服務
.\.venv\Scripts\python.exe test_app.py
```

### 🌐 API 服務

啟動 API 服務後，您可以訪問：

- **服務首頁**: http://localhost:8000
- **API 文件 (Swagger)**: http://localhost:8000/docs
- **API 文件 (ReDoc)**: http://localhost:8000/redoc
- **健康檢查**: http://localhost:8000/health

### 🔧 配置設定

編輯 `.env` 檔案來配置：
- 資料庫連接
- API 服務設定
- JWT 認證設定
- 其他功能參數

### 📝 API 使用範例

1. **登入取得 Token**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

2. **查詢帳號列表**:
```bash
curl -X GET "http://localhost:8000/api/v1/accounts" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

3. **建立登入任務**:
```bash
curl -X POST "http://localhost:8000/api/v1/tasks" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"site_type": "PTT", "account_ids": [1, 2, 3]}'
```

### 🛠️ 故障排除

如果遇到問題：

1. **資料庫連接錯誤**: 檢查 `.env` 中的資料庫設定
2. **模組導入錯誤**: 確認已安裝所有依賴 (自動完成)
3. **端口被占用**: 修改 `.env` 中的 `API_PORT`

### 📂 新增的檔案結構

```
automation-plan/
├── api/                 # API 相關檔案
│   ├── routes/         # API 路由
│   ├── auth.py         # 認證邏輯
│   └── models.py       # 資料模型
├── services/           # 服務層
├── app.py             # FastAPI 主程式
├── run.py             # 統一啟動腳本
├── test_app.py        # 測試服務
├── start.ps1          # PowerShell 啟動腳本
└── .env               # 環境設定檔
```

### 💡 建議

1. **開始使用**: 先執行 `.\start.ps1` 選擇選項 5 測試服務
2. **設定資料庫**: 修改 `.env` 中的資料庫連接資訊
3. **探索 API**: 訪問 http://localhost:8000/docs 查看完整 API 文件
4. **原有功能**: 所有原有的登入發文功能都保持不變

🎉 **恭喜！您的專案現在支援現代化的 Web API 介面了！**
