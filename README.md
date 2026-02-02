# WaveRider Discord Community Bot 🤖

WaveRider 社群的官方 Discord 機器人，提供交易相關功能與社群互動。

## 功能列表

### 交易功能
- `/watchlist` - 管理個人追蹤清單
- `/alert` - 設定價格警報
- `/scan` - 執行股票掃描
- `/quote` - 查詢即時報價

### 社群功能
- `/leaderboard` - 查看排行榜
- `/stats` - 個人統計資料

## 安裝

```bash
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env 設定
python bot.py
```

## 環境變數

| 變數 | 說明 |
|------|------|
| DISCORD_TOKEN | Discord Bot Token |
| DATABASE_URL | PostgreSQL 連線字串 |
| REDIS_URL | Redis 連線字串 |

## 開發

```bash
# 開發模式
python bot.py --dev

# 測試
pytest tests/
```

---
*WaveRider.AI - 讓交易更智能*

<\!-- Updated: Mon Feb  2 07:01:44 PM UTC 2026 -->
