# 🤖 台股 AI 選股系統 · ai-stock-bot（MVP）

> 目標：每日掃描台股、評分排序，透過 LINE / Telegram 推播精選個股，並於收盤後驗證。
> ⚠️ 本 README 只描述**目前已實作、可立即執行**的部分。尚未建立的模組一律標示「⛔ 尚未建立」，不提前描述其內部流程。

-----

## 📦 目前進度（MVP 真實狀態）

|元件                   |檔案                               |狀態    |
|---------------------|---------------------------------|------|
|設定 / env loader      |`config.py`                      |✅ 可用  |
|統一 log               |`utils/logger.py`                |✅ 可用  |
|推播格式（3 種 LOCKED）     |`push/formatter.py`              |✅ 可用  |
|程式入口                 |`main.py`                        |⛔ 尚未建立|
|行情 / 掃描 / 篩選 / 評分    |`core/*`                         |⛔ 尚未建立|
|ML / 回測              |`ml/*`                           |⛔ 尚未建立|
|推播管道（LINE / Telegram）|`push/telegram.py`、`push/line.py`|⛔ 尚未建立|
|資料儲存 / git 同步        |`storage/*`                      |⛔ 尚未建立|
|GitHub Actions 排程    |`.github/workflows/`             |⛔ 尚未建立|


> 因此目前**沒有端到端執行**（無 `main.py`、無排程、不會實際推播）。
> 現在唯一可執行的，是匯入並使用上述三個基礎模組。

-----

## 🎯 專案目的（簡述）

掃描台股 → 評分排序 → 透過 LINE / Telegram 推播精選個股，並於收盤後驗證預測。
（選股、驗證、ML 等完整流程將於後續階段逐模組建立，本文件不提前描述。）

-----

## 🚀 執行方式

### 本機（local）

需求：Python 3。目前三個基礎模組**僅使用標準函式庫**，無外部相依、尚無 `requirements.txt`。

現在可執行的範圍 = 匯入基礎模組（於專案根目錄）：

```python
# 1) 推播格式（純渲染，立即可用）
from push.formatter import format_morning

msg = format_morning(
    "2026/05/28", 0.02, -0.11,
    [{"name": "聚鼎", "code": "6224", "price": 88.70,
      "win_rate": 80.0, "pred": 7.00, "ml_score": 6.3}],
    scanner_count=150, has_ml=True,
)
print(msg)
```

```python
# 2) 設定與環境變數
import config
config.get_env("TG_TOKEN")        # 安全 strip；缺漏回 None
config.normalize_mode("garbage")  # -> ('morning', True)
```

```python
# 3) 統一 log
from utils.logger import get_logger
log = get_logger("main")
log.info("hello")                 # -> [main] hello
```

> 端到端入口 `python main.py` **尚未建立**。

### GitHub Actions

⛔ 排程 workflow **尚未建立**。待 `.github/workflows/` 與 `main.py` 完成後，本節再補上實際排程內容。

-----

## ⚙️ 設定（環境變數）

`config.py` 以 `get_env()` 讀取下列變數，並自動 `strip()` 去除前後空白與隱形換行；缺漏或為空一律回傳 `None`，**不會捏造憑證**。

|變數          |用途                             |必填|
|------------|-------------------------------|--|
|`LINE_TOKEN`|LINE Channel Access Token      |擇一|
|`LINE_ID`   |推播目標 LINE User ID              |擇一|
|`TG_TOKEN`  |Telegram Bot Token             |擇一|
|`TG_CHAT`   |Telegram Chat ID（群組以 `-100` 開頭）|擇一|


> ⚠️ 變數「讀取」已可用，但**消費這些憑證的推播管道模組（`push/telegram.py`、`push/line.py`）尚未建立**，因此目前設定後尚不會實際推播。
> 機密遮罩：`config.mask_secret(token)` 僅顯示前 4 碼（例 `-100...`），供安全輸出。

本機設定範例：

```bash
export TG_TOKEN="your_bot_token"
export TG_CHAT="your_chat_id"
```

-----

## 🧭 MODE 說明

`config.py` 已定義模式白名單與 fallback。`normalize_mode()` 會先 `strip()` 再比對白名單，**非白名單值一律 fallback 為 `morning`**。

|MODE     |規劃用途     |目前狀態                |
|---------|---------|--------------------|
|`morning`|早盤選股推播   |白名單已定義；dispatch 尚未接線|
|`verify` |收盤驗證推播   |同上                  |
|`weekly` |週五週報 / 回測|同上                  |
|`test`   |測試推播     |同上                  |

```python
config.normalize_mode("verify")  # ('verify', False)
config.normalize_mode("")         # ('morning', True)  ← fallback
```

> MODE 的實際分派與各模式行為，將隨 `main.py` 及對應模組建立後才啟用。本文件不提前描述其內部流程。

-----

## 📤 推播格式（formatter 三種 LOCKED format）

以下三種版面由 `push/formatter.py` 定義為**不可變輸出契約（LOCKED）**，僅動態值會變動（版面 / emoji / 分隔線 / 換行 / 全半形括號不得更動）。

**1. 早盤選股 — `format_morning()`**

```
【AI 選股 - AI+Rule 混合模式】
━━━━━━━━━━━━━━
📅 今日預測 2026/05/28
🌍 SPY +0.02% | QQQ -0.11%
━━━━━━━━━━━━━━

🥇 聚鼎 6224 💰88.70
📈 勝率 80.0% | 預測 +7.00% 🤖6.3

🥈 時碩工業 4566 💰67.20
📈 勝率 66.7% | 預測 +4.28% 🤖5.1

🥉 固緯 2423 💰84.80
📈 勝率 75.0% | 預測 +2.17% 🤖4.8

4️⃣ 技嘉 2376 💰337.50
📈 勝率 85.7% | 預測 +2.66% 🤖7.2

5️⃣ 程泰 1583 💰58.70
📈 勝率 55.6% | 預測 +0.56% 🤖3.9
━━━━━━━━━━━━━━
📌 收盤後自動驗證（掃描全市場 150 檔）
```

> 無 ML 模型時，標題改為 `【AI 選股 - 預測模式】`，且各檔不顯示 `🤖` 分數（由呼叫端以 `has_ml` 控制）。

**2. 收盤驗證 — `format_verify()`**

```
📊 預測驗證報告 2026-05-28
✅ 今日準確率: 4/5（80%）

🥇 聚鼎 6224
預測↑(80.0%) | 實際↑ ↑7.12%  ✅ 正確

🥈 時碩工業 4566
預測↑(66.7%) | 實際↑ ↑3.85%  ✅ 正確

🥉 固緯 2423
預測↑(75.0%) | 實際↓ ↓0.24%  ❌ 錯誤

4️⃣ 技嘉 2376
預測↑(85.7%) | 實際↑ ↑1.93%  ✅ 正確

5️⃣ 程泰 1583
預測↑(55.6%) | 實際↑ ↑0.68%  ✅ 正確
```

**3. 週五 ML 回測 — `format_weekly_backtest()`**

```
📊 ML 回測報告（TimeSeriesSplit×5）
樣本總數：<n> 筆
基準勝率（真實）：<x>%
平均準確率：<x>%
平均 AUC：<x>%
特徵重要性：
<由呼叫端傳入的字串，formatter 不解讀其內容>
```

> `format_weekly_backtest()` 只接受基本型別（數值 + 已排版好的特徵字串），不綁定任何 ML 結構。

> 另有 `format_empty / format_paused / format_test / format_weekly_summary`，標記為 **DRAFT — NOT LOCKED**，規格未定、可能刪改，不屬契約。

-----

## ⚠️ 免責聲明

本系統僅供學習與研究用途，所有選股結果不構成投資建議。投資有風險，請自行評估判斷。
