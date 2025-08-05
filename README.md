# 自動登入和發文管理系統 (FastAPI 版本)

## 程式目的

- 各網站登入養帳號 (PTT, CMoney)
- 發文以及推文功能，並且紀錄
- 提供 RESTful API 介面進行管理
- 支援 Web 界面和批次處理兩種模式
- (未來)設定語氣，使用 LLM 進行發文
- (未來)使用 proxy 跳轉 IP 避免 multi-id 被抓

## 新功能 (FastAPI 版本)

### API 服務
- **RESTful API**: 完整的 REST API 介面
- **認證系統**: JWT Token 認證
- **帳號管理**: CRUD 操作管理登入帳號
- **任務管理**: 異步任務執行登入操作
- **日誌查詢**: 查詢登入記錄和統計
- **即時監控**: 任務狀態即時監控

### Web 界面
- **Swagger UI**: `/docs` - 互動式 API 文件
- **ReDoc**: `/redoc` - 美觀的 API 文件
- **健康檢查**: `/health` - 系統狀態檢查

## 安裝和設定

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 環境設定

複製 `.env.example` 為 `.env` 並修改設定：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設定資料庫連接等資訊。

### 3. 初始化資料庫

```bash
python init_db.py
```

這會創建 `users` 表並建立預設管理員帳號：
- 使用者名稱: `admin`
- 密碼: `admin123`

## 使用方式

### API 服務模式 (推薦)

啟動 FastAPI 服務器：

```bash
python run.py --mode api
```

或直接執行：

```bash
python app.py
```

服務將在 `http://localhost:8000` 啟動。

#### 主要 API 端點

- **認證**: `POST /api/v1/auth/login`
- **帳號管理**: `GET/POST/PUT/DELETE /api/v1/accounts`
- **任務管理**: `POST /api/v1/tasks`
- **日誌查詢**: `GET /api/v1/logs`

#### API 使用範例

1. **登入獲取 Token**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

2. **獲取帳號列表**:
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

### 批次處理模式 (向後相容)

執行原始的批次處理：

```bash
python run.py --mode batch
```

### 單一帳號模式

測試單一帳號登入：

```bash
python run.py --mode single --site PTT --account your_account --password your_password
```

## API 文件

啟動服務後可以訪問：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 專案結構

```
automation-plan/
├── api/                    # API 相關檔案
│   ├── routes/            # API 路由
│   │   ├── auth.py       # 認證路由
│   │   ├── accounts.py   # 帳號管理路由
│   │   ├── tasks.py      # 任務管理路由
│   │   └── logs.py       # 日誌查詢路由
│   ├── auth.py           # 認證邏輯
│   └── models.py         # Pydantic 模型
├── services/              # 服務層
│   └── login_service.py  # 登入服務
├── app.py                # FastAPI 主程式
├── run.py                # 啟動腳本
├── init_db.py            # 資料庫初始化
├── config.py             # 設定檔
├── requirements.txt      # Python 依賴
└── .env.example          # 環境變數範例
```

## 原有模組 (保持不變)

以下模組維持原有功能：

- `cmoneyLogin.py` - CMoney 登入邏輯
- `pttLogin.py` - PTT 登入邏輯
- `cmoneyPostModule.py` - CMoney 發文模組
- `pttPostModule.py` - PTT 發文模組
- 其他相關模組...

## 部署建議

### 開發環境

```bash
python run.py --mode api
```

### 生產環境

```bash
# 使用 gunicorn
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用 uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker 部署

可以創建 Dockerfile 進行容器化部署。

## 安全性注意事項

1. **修改預設密碼**: 請立即修改預設管理員密碼
2. **JWT Secret**: 在生產環境中使用強密碼作為 JWT Secret
3. **CORS 設定**: 在生產環境中限制 CORS 來源域名
4. **HTTPS**: 生產環境建議使用 HTTPS

## 故障排除

### 常見問題

1. **資料庫連接失敗**: 檢查 `.env` 中的資料庫設定
2. **模組導入錯誤**: 確保安裝了所有依賴 `pip install -r requirements.txt`
3. **端口被占用**: 修改 `.env` 中的 `API_PORT` 設定

### 日誌查看

- API 日誌: `api.log`
- 系統日誌: `automation_plan.log`

## 開發指南

### 新增 API 端點

1. 在 `api/routes/` 下建立或修改路由檔案
2. 在 `api/models.py` 中定義請求/回應模型
3. 在 `app.py` 中註冊路由

### 新增服務邏輯

1. 在 `services/` 下建立服務檔案
2. 實作業務邏輯
3. 在路由中調用服務

## 版本歷史

- v1.0.0 - FastAPI 版本，新增 API 介面和 Web 管理功能
