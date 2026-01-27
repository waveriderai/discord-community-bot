# WaveRider Discord Community Bot

智慧化 Discord 社群管理機器人，整合 Claude AI 提供交易策略問答服務。

## 功能

### Phase 1 MVP (目前)
- `/ping` - 檢查機器人狀態
- `/help` - 顯示指令列表
- `/about` - 關於本機器人
- `/ask <問題>` - Claude AI 智慧問答
- 新成員自動歡迎

### Phase 2 (開發中)
- 交易訊號自動推播
- MariaDB 整合
- N8N Webhook

## 快速開始

### 本地開發

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的 tokens

# 執行
python bot.py
```

### Docker 部署

```bash
# 本地測試
docker compose up --build

# 背景執行
docker compose up -d --build
```

### Portainer Git Deploy

1. Portainer > Stacks > Add Stack
2. 選擇 "Repository"
3. 填入 Git URL
4. Compose path: `docker-compose.yml`
5. 設定環境變數 (Environment variables)
6. Deploy

**需要設定的環境變數：**
- `DISCORD_TOKEN` - Discord Bot Token
- `ANTHROPIC_API_KEY` - Claude API Key

## 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `DISCORD_TOKEN` | ✅ | Discord Bot Token |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API Key |
| `CLAUDE_MODEL` | ❌ | Claude 模型 (預設: claude-sonnet-4-20250514) |
| `BOT_PREFIX` | ❌ | 指令前綴 (預設: !) |
| `LOG_LEVEL` | ❌ | 日誌等級 (預設: INFO) |

## 專案結構

```
discord-community-bot/
├── bot.py              # 主程式
├── requirements.txt    # Python 依賴
├── Dockerfile          # Docker 映像
├── docker-compose.yml  # Docker Compose
├── .env.example        # 環境變數範例
├── .env                # 環境變數 (不進版控)
├── PRD.md              # 產品需求文件
└── README.md           # 本文件
```

## 開發筆記

### Discord Bot 設定

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 建立 Application
3. Bot > Reset Token > 複製 Token
4. OAuth2 > URL Generator:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Read Message History`, `Use Slash Commands`
5. 使用產生的 URL 邀請 Bot 到你的 Server

### Claude API

1. 前往 [Anthropic Console](https://console.anthropic.com/)
2. 建立 API Key
3. 填入 `.env` 的 `ANTHROPIC_API_KEY`

## License

Private - WaveRider Team
