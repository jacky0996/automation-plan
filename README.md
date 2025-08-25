# 🤖 Automation Plan - 多平台自動化管理系統

> 一個集成 PTT 和 CMONEY 平台的自動化管理系統，支援帳號登入管理、自動發文、推文等功能。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 目錄

- [✨ 功能特色](#-功能特色)
- [🏗️ 系統架構](#️-系統架構)
- [📦 安裝指南](#-安裝指南)
- [⚙️ 配置設定](#️-配置設定)
- [🚀 使用方法](#-使用方法)
- [📊 資料庫結構](#-資料庫結構)
- [📁 專案結構](#-專案結構)
- [🔧 開發說明](#-開發說明)
- [⚠️ 注意事項](#️-注意事項)

## ✨ 功能特色

### 🔐 帳號管理
- **多平台支援**：支援 PTT 和 CMONEY 平台
- **自動登入**：智能排程登入系統，避免帳號閒置
- **登入記錄**：完整的登入日誌追蹤
- **帳號狀態管理**：動態啟用/停用帳號

### 📝 內容管理
- **自動發文**：支援 PTT 和 CMONEY 平台發文
- **推文功能**：自動推文系統
- **內容模板**：可自定義發文和推文模板
- **股票資訊**：CMONEY 平台股票討論區自動化

### 📈 數據分析
- **熱門文章追蹤**：PTT 熱門文章監控
- **活動日誌**：完整的操作記錄
- **任務排程**：靈活的任務調度系統
- **執行報告**：詳細的執行結果統計

### 🚀 未來規劃
- **LLM 集成**：使用 AI 進行智能發文和語氣設定
- **IP 代理**：支援 Proxy 跳轉避免多帳號檢測
- **更多平台**：擴展支援更多社群平台

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main System   │    │   PTT Module    │    │  CMONEY Module  │
│                 │────│                 │    │                 │
│  ┌─────────────┐│    │  ┌─────────────┐│    │  ┌─────────────┐│
│  │ Login Mgr   ││    │  │ PTT Login   ││    │  │CMONEY Login ││
│  └─────────────┘│    │  └─────────────┘│    │  └─────────────┘│
│  ┌─────────────┐│    │  ┌─────────────┐│    │  ┌─────────────┐│
│  │ Task Mgr    ││    │  │ PTT Post    ││    │  │CMONEY Post  ││
│  └─────────────┘│    │  └─────────────┘│    │  └─────────────┘│
│  ┌─────────────┐│    │  ┌─────────────┐│    │  ┌─────────────┐│
│  │ DB Manager  ││    │  │ PTT Push    ││    │  │CMONEY Push  ││
│  └─────────────┘│    │  └─────────────┘│    │  └─────────────┘│
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                        ┌─────────────────┐
                        │   MySQL DB      │
                        │                 │
                        │ ┌─────────────┐ │
                        │ │  accounts   │ │
                        │ │ login_logs  │ │
                        │ │   posts     │ │
                        │ │ push_tasks  │ │
                        │ │    ...      │ │
                        │ └─────────────┘ │
                        └─────────────────┘
```

## 📦 安裝指南

### 環境需求
- Python 3.8+
- MySQL 8.0+
- Chrome/Chromium 瀏覽器

### 1. 克隆專案
```bash
git clone https://github.com/jacky0996/automation-plan.git
cd automation-plan
```

### 2. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

### 4. 安裝 Playwright 瀏覽器
```bash
playwright install chromium
```

### 5. 建立資料庫
```bash
mysql -u root -p < automation_plan.sql
```

## ⚙️ 配置設定

### 1. 環境變數設定
創建 `.env` 檔案：
```env
# 資料庫設定
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=automation_plan

# 瀏覽器設定
HEADLESS_BROWSER=True
```

### 2. 帳號設定
在 `accounts` 資料表中新增要管理的帳號：
```sql
INSERT INTO accounts (account, password, account_type, status) 
VALUES ('your_account', 'your_password', 'PTT', 1);
```

## 🚀 使用方法

### 基本執行
```bash
python main.py
```

### 主要模組說明

#### 🔐 登入管理
```bash
# PTT 登入
python pttLogin.py

# CMONEY 登入
python cmoneyLogin.py
```

#### 📝 發文功能
```bash
# PTT 發文
python pttPostModule.py

# CMONEY 發文
python cmoneyPostModule.py
```

#### 👍 推文功能
```bash
# PTT 推文
python pttPushModule.py

# CMONEY 推文（設定貼文）
python cmoneySetPostModule.py
```

#### 📊 數據收集
```bash
# PTT 熱門文章
python pttHotScraper.py

# CMONEY 股票爬蟲
python cmoneyStockScraper.py
```

## 📊 資料庫結構

### 核心資料表

| 資料表 | 說明 | 主要欄位 |
|--------|------|----------|
| `accounts` | 帳號管理 | id, account, password, account_type, status |
| `login_logs` | 登入記錄 | account_id, login_time, status, message |
| `posts` | 發文記錄 | account_id, board, title, content, platform |
| `push_tasks` | 推文任務 | account_id, post_id, push_content, status |
| `activity_log` | 活動日誌 | account_id, action, action_time, status |
| `scheduled_tasks` | 排程任務 | account_id, task_type, next_execution_time |

### 平台特定資料表

#### PTT 相關
- `ptt_get_post_by_board` - 看板文章搜尋設定
- `ptt_push_post` - PTT 推文設定

#### CMONEY 相關
- `cmoney_get_board_by_popular` - 熱門股票追蹤
- `cmoney_push_post` - CMONEY 推文設定

#### 共用設定
- `replay_template` - 推文模板管理

## 📁 專案結構

```
automation-plan/
├── 📄 main.py                      # 主程式入口
├── ⚙️ config.py                   # 配置管理
├── 📊 automation_plan.sql          # 資料庫結構
├── 📋 requirements.txt             # 依賴套件
├── 📝 README.md                   # 專案說明
├── 🚫 .gitignore                  # Git 忽略檔案
│
├── 🔐 PTT 模組/
│   ├── pttBase.py                 # PTT 基礎類別
│   ├── pttLogin.py                # PTT 登入主程式
│   ├── pttLoginModule.py          # PTT 登入模組
│   ├── pttPostModule.py           # PTT 發文模組
│   ├── pttPushModule.py           # PTT 推文模組
│   ├── pttHotScraper.py           # PTT 熱門文章爬蟲
│   ├── pttSearchPosts.py          # PTT 文章搜尋
│   └── pttSetRandomPushModule.py  # PTT 隨機推文設定
│
├── 💰 CMONEY 模組/
│   ├── cmoneyBase.py              # CMONEY 基礎類別
│   ├── cmoneyLogin.py             # CMONEY 登入主程式
│   ├── cmoneyLoginModule.py       # CMONEY 登入模組
│   ├── cmoneyPostModule.py        # CMONEY 發文模組
│   ├── cmoneySetPostModule.py     # CMONEY 設定貼文模組
│   └── cmoneyStockScraper.py      # CMONEY 股票爬蟲
│
├── 🛠️ 工具模組/
│   ├── loginManager.py            # 登入管理器
│   └── dailyReport.py             # 每日報告
│
└── 📁 logs/                       # 日誌檔案目錄
```

## 🔧 開發說明

### 新增平台支援
1. 建立平台基礎類別（繼承 `BaseBot`）
2. 實作登入、發文、推文模組
3. 在 `main.py` 中新增平台處理邏輯
4. 更新資料庫結構（如需要）

### 自定義功能
- **登入邏輯**：修改 `*LoginModule.py` 檔案
- **發文模板**：更新 `replay_template` 資料表
- **排程設定**：調整 `main.py` 中的時間計算邏輯

### 日誌系統
- 所有操作都會記錄在 `logs/` 目錄
- 支援檔案和控制台雙重輸出
- 可透過 `config.py` 調整日誌等級

## ⚠️ 注意事項

### 🔒 安全提醒
- **敏感資訊**：請勿在程式碼中硬編碼帳號密碼
- **環境變數**：使用 `.env` 檔案管理機敏設定
- **權限控制**：確保資料庫連線使用適當權限

### 📖 使用規範
- **合法使用**：請遵守各平台的使用條款
- **頻率控制**：避免過於頻繁的操作
- **內容審查**：確保發布內容符合平台規範

### 🐛 常見問題
- **瀏覽器問題**：確保 Chromium 正確安裝
- **網路連線**：檢查防火牆和代理設定
- **資料庫連線**：確認資料庫服務正常運行

### 🔄 維護建議
- 定期備份資料庫
- 監控日誌檔案大小
- 更新依賴套件版本
- 檢查帳號狀態

---


