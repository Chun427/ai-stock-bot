# 🤖 台股全市場 AI 選股系統 · ai-stock-bot

每日自動掃描上市＋上櫃全市場候選，結合技術分析、歷史回測勝率與機器學習評分，
透過 **LINE Messaging API / Telegram Bot** 推播精選潛力股；每週五自動重訓 ML 模型。
另內建 **回測模式（backtest）** 可用真實歷史資料驗證策略是否具超額報酬。

---

## 目錄

- [系統架構](#系統架構)
- [觸發架構](#觸發架構)
- [執行模式](#執行模式)
- [推播畫面範例](#推播畫面範例)
- [選股 Universe](#選股-universe)
- [5 日波段標記規則](#5-日波段標記規則)
- [ML 模型](#ml-模型)
- [回測模式（backtest）](#回測模式backtest)
- [檔案結構](#檔案結構)
- [環境設定（Secrets / 權限）](#環境設定secrets--權限)
- [部署與準時觸發](#部署與準時觸發)
- [系統狀態與已知限制](#系統狀態與已知限制)
- [免責聲明](#免責聲明)

---

## 系統架構

```
外部準時排程器（Google Apps Script / cron-job.org …）
        │  每日 09:00 打 GitHub API
        ▼
repository_dispatch  ──►  GitHub Actions（stock.yml）
                                │
                                ▼
                        scheduler.py（唯一 MODE 解析）
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        run_morning        run_verify        run_weekly
              │                 │                 │
   scanner→filter→scorer   verifier（5日標記）  weekly報表＋ML重訓＋回測
              │                 │                 │
              ▼                 ▼                 ▼
        push/formatter（推播格式唯一定義處）
              │
        ┌─────┴─────┐
        ▼           ▼
   Telegram        LINE
              │
              ▼
   storage：db.json / history.csv / model.pkl（git_sync 回寫 repo）
```

資料流的每個模式最後都會輸出 `[REPORT]`（mode / scanner / filter / final /
push_telegram / push_line / db_update），作為每次執行的可觀測性紀錄。

---

## 觸發架構

> **重要工程事實：GitHub Actions 的 `schedule`（cron）不是準時系統。**
> 官方定義為 best-effort，高負載時可能延遲數小時甚至丟棄；實測本專案
> morning 連續多日延遲約 3.5–4.8 小時（09:00 排程 → 實際約 13:00 才觸發）。
> 因此 cron 僅作**備援**，**準時來源改由外部排程器**負責。

系統支援三種觸發來源（皆由 `scheduler.py` 統一解析 MODE）：

| 觸發來源 | 用途 | 準時性 |
|---|---|---|
| `repository_dispatch`（外部排程器打 API） | **主要**：準時觸發 | ✅ ±1–2 分鐘 |
| `schedule`（GitHub cron） | 備援：外部觸發失效時仍會跑（延遲） | ❌ 會延遲/漏跑 |
| `workflow_dispatch`（手動） | 測試 `test` / 執行 `backtest` | 即時 |

**repository_dispatch 事件對應：**

| event_type | MODE | 台灣時間 |
|---|---|---|
| `morning_run` | morning | 09:00（週一~五） |
| `verify_run` | verify | 14:45（週一~四） |
| `weekly_run` | weekly | 週五 20:00 |

**`scheduler.py` = 單一時間/MODE 來源。** 所有「schedule → MODE」「dispatch → MODE」
對應只定義於此檔；workflow 只呼叫 `python scheduler.py "<schedule>" "<input>" "<action>"`，
`config.py` 的合法模式白名單也 import 自此，避免多頭維護。

**備援 cron（僅在外部觸發失效時作用）：**

| cron (UTC) | MODE | 台灣時間 |
|---|---|---|
| `0 1 * * 1-5` | morning | 09:00 |
| `45 6 * * 1-4` | verify | 14:45 |
| `0 12 * * 5` | weekly | 週五 20:00 |

---

## 執行模式

| MODE | 說明 |
|---|---|
| `morning` | 掃描候選 → 技術+ML 評分 → 推播前 5 名；特徵寫入 `history.csv` |
| `verify` | 驗證已達 5 交易日之預測 → 5 日波段標記 → 回填標籤 → 推播結果 |
| `weekly` | 當日驗證 + 週報 + 重訓 ML + 回測報告 |
| `test` | 推播測試訊息，確認 Token 與管道 |
| `backtest` | **離線**：真實歷史 walk-forward 回測 + 基準比較 + 成本，輸出 CSV/報告（不推播） |

CLI 覆蓋：`python main.py --mode backtest`（MODE 合法性由 `scheduler.py` 裁定）。

---

## 推播畫面範例

> 以下為 `push/formatter.py` 實際產生的推播內容（示意資料）。所有格式的唯一來源即
> `push/formatter.py`，其他模組禁止自行拼字串。

### 早盤選股（morning）

```
【AI 選股 - 預測模式】
━━━━━━━━━━━━━━
📅 今日預測 2026/07/01
🌍 SPY +0.79% | QQQ +1.70%
━━━━━━━━━━━━━━
🥇 祥碩 5269 💰1490.00
📈 勝率 40.0% | 預測 +3.16%
🥈 兆豐金 2886 💰46.40
📈 勝率 38.5% | 預測 +2.12%
🥉 安普新 6743 💰31.90
📈 勝率 37.0% | 預測 +2.24%
4️⃣ 洋基工程 6691 💰757.00
📈 勝率 43.5% | 預測 +3.50%
5️⃣ 威宏-KY 8442 💰42.25
📈 勝率 66.7% | 預測 +3.84%
━━━━━━━━━━━━━━
📌 收盤後自動驗證(掃描全市場 230 檔)
```

### 收盤驗證（verify）

```
━━━━━━━━━━━━━━
📊 預測驗證報告 2026-07-01
✅ 今日準確率: 2/3(67%)
━━━━━━━━━━━━━━
🥇 祥碩 5269
預測↑(40.0%) | 實際↑ ↑4.12%  ✅ 正確
🥈 兆豐金 2886
預測↑(38.5%) | 實際↓ ↓0.86%  ❌ 錯誤
🥉 安普新 6743
預測↑(37.0%) | 實際↑ ↑3.55%  ✅ 正確
━━━━━━━━━━━━━━
```

### 週報（weekly）

```
━━━━━━━━━━━━━━
📈 本週準確率週報 2026-07-04
✅ 本週累計: 11/18(61%)
━━━━━━━━━━━━━━
```

### 週五 ML 回測報告（weekly）

```
【ML 回測報告】
━━━━━━━━━━━━━━
樣本總數:1200 筆
基準勝率(真實):52.3%
平均準確率:61.8%
平均 AUC:67.0%
━━━━━━━━━━━━━━
```

### 測試訊息（test）

```
━━━━━━━━━━━━━━
✅ ai-stock-bot 推播測試
Token 與推播管道正常
時間 2026-07-02 09:00
━━━━━━━━━━━━━━
```

### 其他 fail-safe 畫面

無符合標的時（仍推播，不靜默）：

```
【AI 選股 - 預測模式】
━━━━━━━━━━━━━━
📅 今日預測 2026/07/01
🌍 SPY +0.79% | QQQ +1.70%
━━━━━━━━━━━━━━
😶 今日無符合條件之標的
━━━━━━━━━━━━━━
📌 收盤後自動驗證(掃描全市場 230 檔)
```

美股大跌暫停選股：

```
【AI 選股 - 預測模式】
━━━━━━━━━━━━━━
📅 今日預測 2026/07/01
🌍 SPY -0.62% | QQQ -1.20%
━━━━━━━━━━━━━━
⚠️ 美股大跌，今日暫停選股
━━━━━━━━━━━━━━
```

---

## 選股 Universe

**現行 production universe（Universe B，動量候選）：**
TWSE 上市 ＋ TPEx 上櫃，4 位數字代號，**昨日上漲**，依漲幅取前 `MAX_CANDIDATES`（=230）。

> ⚠️ **「掃描全市場 230 檔」中的 230 是「上限（cap）」，不是市場總數。**
> 當日上漲家數常 >230，被截斷為漲幅前 230。此設計偏動量，屬已知特性。

**已知混入項（預設不排除，可切換）：**

| 開關（config.py） | 預設 | 作用 |
|---|---|---|
| `EXCLUDE_ETF` | `False` | 設 `True` 排除 00 開頭 ETF（如 0050/0056/00878） |
| `EXCLUDE_KY` | `False` | 設 `True` 排除 -KY 外國企業（如 臻鼎-KY 4958） |

權證/牛熊證（非 4 位數字）天然排除；興櫃不在來源。**處置股/停牌/全額交割目前未自動排除**（來源未標記），列為已知風險。

**Universe A（全市場，回測用）**：由 `core/universe.py` 提供，優先讀
`data/universe.csv`（單欄代號），無則用內建代表性樣本清單（會標記非全市場）。

---

## 5 日波段標記規則

- 買入後最多 5 個交易日，任一日 High 漲幅 > **+3%** 且未先觸停損 → 命中（`label=1`）
- 期間任一日 Low 跌幅 ≤ **−1.5%** → 強制失敗（`label=0`，即使後來漲回）
- 結果回填 `history.csv` 之 `target_label`，作為 ML 訓練標籤

---

## ML 模型

- `RandomForestClassifier`（100 棵、`max_depth=5`）
- 特徵：`rsi, vx, chg, ma20_diff, hi_lo_pos, weekday`
- 最低訓練門檻 **30 筆**有標籤樣本；不足時退為純 Rule-based，推播不中斷
- 週五 `TimeSeriesSplit×5` 回測（no shuffle，防未來資料洩露）
- **三層輸出**：
  - **USER**：乾淨推播（結果＋指標＋排名，不含任何 ML 術語）
  - **MODEL**：特徵重要性 / CV / training log —— 僅記 log，不推播
  - **DEBUG**：error / raw prediction

---

## 回測模式（backtest）

用真實歷史資料驗證「選股是否真的優於基準」，**扣除台股交易成本**避免高估。

- **無未來資料洩漏**：第 t 期選股只用 `≤ t` 的資料，評估看 `t+1…t+HOLD`
- **非重疊週再平衡**（每 5 交易日一期），可正確計算年化 / Sharpe / MDD
- **交易成本**（`ml/costs.py`）：手續費 0.1425%×2 + 證交稅 0.3% + 滑價 0.1%×2
- **三基準比較**：隨機選股 / 全 universe 等權 / 指數買進持有（0050.TW）
- **輸出**（`data/backtests/`）：每筆交易 CSV ＋ Markdown 報告
  （總報酬、年化、Sharpe、最大回撤、勝率、Precision@5、對指數超額報酬）

執行（需可連網環境，會抓 yfinance 歷史）：

```bash
python main.py --mode backtest
# 可選：於 data/universe.csv 放完整股票清單作為回測 universe
```

相關參數（`config.py`）：`BT_YEARS=4`、`BT_HOLD_DAYS=5`、`BT_TOP_N=5`、`BT_INDEX_TICKER=0050.TW`。

---

## 檔案結構

```
main.py                MODE 分派 + [REPORT] + --mode CLI
scheduler.py           單一時間/MODE 來源（schedule / dispatch / 手動）
config.py              環境變數 / 常數 / 路徑 / 成本 / 回測參數
core/
  scanner.py           TWSE + TPEx 候選掃描（含 universe 排除開關）
  universe.py          雙層 universe（A 回測 / B production）
  filter.py            技術特徵計算與濾網
  scorer.py            62 日回測勝率評分
  verifier.py          5 日波段標記 + 回填
  market_data.py       yfinance 包裝（含 timeout / 降級）
  weekly_report.py     週報彙總
ml/
  ml_model.py          模型載入 + 預測（無模型→rule-based）
  trainer.py           RandomForest 重訓
  backtest.py          週五 TimeSeriesSplit×5（線上）
  backtest_engine.py   離線 walk-forward 回測引擎 + 基準 + 報告
  walkforward.py       walk-forward 邏輯（含合成自測）
  costs.py             台股交易成本模型
push/
  formatter.py         推播格式唯一定義（契約）
  telegram.py          Telegram 推播（retry / 200 才算成功）
  line.py              LINE 推播（retry / fail-fast）
storage/
  db.py                db.json 讀寫（atomic）
  history.py           history.csv 特徵 / 標籤
  git_sync.py          Actions 內 commit 狀態回 repo
utils/logger.py        統一 log 格式
data/                  db.json / history.csv / model.pkl(自動) / backtests/
.github/workflows/stock.yml
trigger.gs             （外部）Google Apps Script 準時觸發器
```

---

## 環境設定（Secrets / 權限）

| Secret | 說明 | 必填 |
|---|---|---|
| `LINE_TOKEN` | LINE Channel Access Token | 擇一 |
| `LINE_ID` | 推播目標 User ID | 擇一 |
| `TG_TOKEN` | Telegram Bot Token | 擇一 |
| `TG_CHAT` | Telegram Chat ID（群組以 `-100` 開頭） | 擇一 |

> **Settings → Actions → General → Workflow permissions** 須設為 **Read and write**，
> 讓 Actions 能 commit `db.json` / `history.csv` / `model.pkl` 回 repo。

---

## 部署與準時觸發

**1. Repo 端**：Secrets 與 Workflow 權限設定如上；`stock.yml` 已支援 `repository_dispatch`。

**2. 準時觸發（關鍵）**：因 GitHub cron 不準時，需外部排程器打 API。推薦
Google Apps Script（`trigger.gs`）：

1. 建立 GitHub **Fine-grained PAT**（僅本 repo、Contents: Read and write）
2. 於 [script.google.com](https://script.google.com) 貼上 `trigger.gs`，填入 PAT，時區設 Taipei
3. 執行 `testNow` 驗證（Actions 應出現 `event=repository_dispatch`）
4. 執行 `setupTriggers` 建立每日排程（morning 09:00 / verify 14:45 / weekly 五 20:00）

> 手動觸發（免外部排程器，測試用）：
> ```bash
> curl -X POST -H "Authorization: Bearer <PAT>" \
>   -H "Accept: application/vnd.github+json" \
>   https://api.github.com/repos/<owner>/ai-stock-bot/dispatches \
>   -d '{"event_type":"morning_run"}'
> ```

---

## 系統狀態與已知限制

| 項目 | 狀態 |
|---|---|
| Python / pipeline | ✅ 正常 |
| 推播（LINE / Telegram） | ✅ 已驗證（HTTP 200 + 實收） |
| Workflow / scheduler / dispatch | ✅ 已部署 |
| 準時觸發（09:00） | ⚠️ 需外部排程器；純 GitHub cron 會延遲 3–4 小時 |
| **策略有效性（是否具 Alpha）** | ❌ **尚未驗證** — 需以真實資料執行 `backtest` 並優於基準才成立 |

> 目前的「勝率」為 62 日同期樣本內統計，非未來預測力；在回測（模型 vs 隨機 vs 0050）
> 證明持續超額報酬之前，**不應視為具投資優勢**。

---

## 免責聲明

本系統僅供學習研究，選股結果**不構成投資建議**。歷史回測不保證未來績效，
投資有風險，請自行評估並承擔後果。
