# 🤖 台股 AI 選股系統 · ai-stock-bot

每個交易日自動掃描台股（上市＋上櫃）候選股，以**規則式策略**評分排序，
推播前 5 名至 **Telegram / LINE**，並於 5 個交易日後自動驗證結果、累積訓練資料。

> ⚠️ **請先讀這一段**：本專案目前是**研究型專案**，不是已證明獲利的自動交易系統。
> 機器學習模型**尚未投入 Production**，回測**尚未執行**，命中率與 Alpha **目前皆未知**。
> 詳見 [今天能證明什麼](#今天能證明什麼what-this-project-can-prove-today)。

---

## 目錄

- [系統架構（Current Architecture）](#系統架構current-architecture)
- [每日執行流程（Current Runtime Flow）](#每日執行流程current-runtime-flow)
- [觸發架構](#觸發架構)
- [執行模式](#執行模式)
- [推播畫面範例](#推播畫面範例)
- [推播的股票代表什麼](#推播的股票代表什麼)
- [驗證狀態（Current Validation Status）](#驗證狀態current-validation-status)
- [資料品質狀態（Data Quality Status）](#資料品質狀態data-quality-status)
- [ML 狀態（ML Status）](#ml-狀態ml-status)
- [回測狀態（Backtest Status）](#回測狀態backtest-status)
- [Virtual Decision Panel 狀態](#virtual-decision-panel-狀態)
- [工程治理狀態（Governance Status）](#工程治理狀態governance-status)
- [已知限制（Current Limitations）](#已知限制current-limitations)
- [今天能證明什麼（What This Project Can Prove Today）](#今天能證明什麼what-this-project-can-prove-today)
- [今天還不能證明什麼（What It Cannot Prove Yet）](#今天還不能證明什麼what-it-cannot-prove-yet)
- [待辦事項（Pending Items）](#待辦事項pending-items)
- [檔案結構](#檔案結構)
- [環境設定](#環境設定)
- [免責聲明](#免責聲明)

---

## 系統架構（Current Architecture）

```
Google Apps Script（外部排程器，唯一時間來源）
        │  09:00 / 14:45 / 週五 20:00（台北時區）
        ▼
repository_dispatch  →  GitHub Actions（stock.yml）
        ▼
scheduler.py（MODE 解析唯一來源）
        │
   ┌────┴────┬─────────┐
   ▼         ▼         ▼
morning   verify    weekly
   │         │         │
   └────► push/formatter → Telegram + LINE
                 │
                 ▼
     data/history.csv（ML 訓練唯一來源）
     data/db.json（預測紀錄）
                 │
          git_sync 回寫 repo
```

**GitHub Actions cron 已停用**（實測延遲 3–4 小時），準時性由外部排程器負責。

---

## 每日執行流程（Current Runtime Flow）

每個交易日早上（morning 模式）實際執行的流程：

| # | 步驟 | 程式位置 | 狀態 |
|---|---|---|---|
| 1 | **Trading Day Guard** | `main.py::_is_trading_day()` | ✅ 已實作（非交易日直接略過，不掃描、不推播、不寫入） |
| 2 | 美股大跌檢查 | `core/market_data.py` | ✅ 已實作（SPY/QQQ 大跌 → 暫停選股） |
| 3 | **Scanner**（TWSE + TPEx 候選） | `core/scanner.py` | ✅ 已實作 |
| 4 | **Filter**（技術特徵 + 濾網） | `core/filter.py` | ✅ 已實作 |
| 5 | **Rule Scoring**（62 日回測勝率） | `core/scorer.py` | ✅ 已實作 **← 目前真正的決策核心** |
| 6 | **ML Scoring** | `ml/ml_model.py::predict_score()` | ⚠️ **程式已呼叫，但 `model.pkl` 不存在 → 恆回傳 `None`，實際不影響選股** |
| 7 | **Virtual Decision Panel** | — | ❌ **NOT IMPLEMENTED**（僅存在於治理流程，無任何程式碼） |
| 8 | **Ranking**（取前 `TOP_N` = 5） | `main.py` | ✅ 已實作 |
| 9 | **Push**（Telegram / LINE） | `push/formatter.py`, `telegram.py`, `line.py` | ✅ 已實作 |
| 10 | 寫入 `history.csv` | `storage/history.py`（含去重） | ✅ 已實作 |
| 11 | 寫入 `db.json` + git 回寫 | `storage/db.py`, `git_sync.py` | ✅ 已實作 |

> **關鍵事實**：步驟 6 的 ML 目前**不參與任何決策**。每日推播的 5 檔股票，
> **完全由步驟 3–5 的規則式流程產生**。

---

## 觸發架構

> **重要工程事實：GitHub Actions 的 `schedule`（cron）不是準時系統。**
> 官方定義為 best-effort；實測本專案 morning 連續多日延遲約 **3.5–4.8 小時**
> （09:00 排程 → 實際約 13:00 才觸發）。因此 **cron 已停用**，準時來源改由外部排程器負責。

| 觸發來源 | 用途 | 準時性 |
|---|---|---|
| `repository_dispatch`（外部排程器打 GitHub API） | **唯一正式入口** | ✅ 實測 ±1–3 分鐘 |
| `schedule`（GitHub cron） | **已停用**（workflow 內註解保留，僅供 rollback） | ❌ 延遲 3–4 小時 |
| `workflow_dispatch`（手動） | 測試 `test` / 執行 `backtest` | 即時 |

**event_type 對應：**

| event_type | MODE | 台灣時間 |
|---|---|---|
| `morning_run` | morning | 09:00（週一~五） |
| `verify_run` | verify | 14:45（週一~四） |
| `weekly_run` | weekly | 週五 20:00 |

**`scheduler.py` = 單一 MODE 解析來源。** workflow 只呼叫
`python scheduler.py "<schedule>" "<input>" "<action>"`，避免多頭維護。

**外部排程器**：Google Apps Script（`trigger.gs`，不在本 repo，存於個人 Google 帳號），
內含 PAT（Script Properties）、retry×3、結構化 log、失敗告警、交易日判斷。

---

## 推播畫面範例

> 以下為 `push/formatter.py` **實際產生**的輸出（示意資料）。推播格式的唯一來源即此檔。

### 早盤選股（morning）

```
【AI 選股 - 預測模式】
━━━━━━━━━━━━━━
📅 今日預測 2026/07/13
🌍 SPY +0.00% | QQQ -1.73%
━━━━━━━━━━━━━━
🥇 崇越 5434 💰531.00
📈 勝率 53.3% | 預測 +3.25%
🥈 聯策 6658 💰208.50
📈 勝率 54.2% | 預測 +4.95%
🥉 麗正 2302 💰52.00
📈 勝率 43.2% | 預測 +6.22%
4️⃣ 精成科 6191 💰108.00
📈 勝率 52.6% | 預測 +4.62%
5️⃣ 盟立 2464 💰172.50
📈 勝率 38.7% | 預測 +4.62%
━━━━━━━━━━━━━━
📌 收盤後自動驗證(掃描全市場 198 檔)
```

> ⚠️ 畫面中的「勝率」為**過去 62 日規則式統計**，「預測」為規則式估算漲幅——
> **兩者皆非 ML 模型輸出**（ML 尚未上線，見 [ML 狀態](#ml-狀態ml-status)）。

### 收盤驗證（verify，無到期標的時）

```
━━━━━━━━━━━━━━
📊 預測驗證報告 2026-07-13
✅ 今日準確率: 0/0(0%)
━━━━━━━━━━━━━━
```

「今日無到期可驗證之預測」是**正常狀態**——代表當日沒有任何預測剛好滿 5 個交易日。

---

## 推播的股票代表什麼

依 `config.py` 與 `core/verifier.py` 的實際定義：

| 項目 | 定義 |
|---|---|
| **交易型態** | **短波段（Swing Trade）** — 非當沖、非隔日沖 |
| **基準價** | 推播當日的**前一交易日收盤價** |
| **持有期** | 最多 **5 個交易日**（`VERIFY_WINDOW = 5`） |
| **停利** | 任一日最高價 ≥ 基準價 **+3%**（`HIT_THRESHOLD = 0.03`）→ 命中 |
| **停損** | 任一日最低價 ≤ 基準價 **−1.5%**（`STOP_THRESHOLD = -0.015`）→ 失敗（優先於停利） |
| **時間出場** | 5 日內皆未觸發 → 第 5 日收盤 |
| **命中定義** | 5 日內先觸 +3% 且未先觸 −1.5% → `target_label = 1` |

推播畫面的「勝率 xx%」= **過去 62 日同期樣本的規則式統計**，**不是**模型的未來預測力。

---

## 驗證狀態（Current Validation Status）

| 驗證項目 | 狀態 | 說明 |
|---|---|---|
| 推播管線（Telegram / LINE） | ✅ 已驗證 | HTTP 200 + `ok=true` 才算成功 |
| 準時觸發（±15 分） | ✅ 已驗證 | 連續 5 個交易日 ±3 分鐘內 |
| Trading Day Guard | ✅ 已驗證 | 週六/日 → 不執行 |
| Dedup Guard | ✅ 已驗證 | 同 `(date, code)` 重複寫入被跳過 |
| Data Validator | ✅ 已驗證 | 可偵測重複鍵 / 非交易日 / 缺值 / 數值異常 |
| Training Gate | ✅ 已驗證 | 資料不合格 → 拒絕訓練（不修改資料） |
| **模型命中率** | ❌ **未知** | 見下方 ML Status |
| **策略 Alpha** | ❌ **未知** | 見下方 Backtest Status |

---

## 資料品質狀態（Data Quality Status）

**`data/history.csv` 目前含 12 列髒資料（尚未清理）：**

| 問題 | 數量 |
|---|---|
| 重複鍵 `(2026-07-03, 6589)`、`(2026-07-03, 6658)` | 2 列 |
| 非交易日資料（2026-07-04 六、2026-07-05 日） | 10 列 |
| **合計** | **12 / 64 = 18.8%** |

**已部署的防護（Gate-A）**：
- `data_validator.py` — 資料品質檢查（唯讀，不修改資料）
- `storage/history.py` — 寫入前以 `(date, code)` 去重
- `main.py` — 交易日 guard（Python 端最後防線，不依賴 GAS）
- `ml/trainer.py` — Training Gate：資料不合格則**拒絕訓練**

**清理狀態**：⏸ **Pending（CP2）** — 清理腳本 `scripts/clean_history.py` 已就緒，
但依治理流程須經核准後方可執行 `--replace`。**目前 `history.csv` 仍為原始 64 列。**

> ⚠️ **連鎖效應**：因資料仍不合格，Training Gate 會**拒絕所有訓練**。
> 這是設計如此（不以髒資料訓練），也代表**資料清理是 ML 上線的前置條件**。

---

## ML 狀態（ML Status）

| 項目 | 狀態 |
|---|---|
| RandomForest 訓練程式 | ✅ 存在（`ml/trainer.py`） |
| **`model.pkl`** | ❌ **不存在** |
| **ML 是否投入 Production** | ❌ **NO** |
| ML 是否參與過任何一次選股 | ❌ **從未** |
| 有標籤樣本 | **19 筆**（訓練門檻 `ML_MIN_LABELS = 30`，尚差 11 筆） |
| 目前決策方式 | **規則式（Rule-Based）** |

`ml_model.predict_score()` 在流程中被呼叫，但因無模型而恆回傳 `None`，
系統 fallback 至規則式評分。**這是誠實的設計（推播不中斷），但也表示 ML 尚未產生任何影響。**

---

## 回測狀態（Backtest Status）

| 項目 | 狀態 |
|---|---|
| 回測引擎 | ✅ 存在（`ml/backtest_engine.py`, `ml/walkforward.py`） |
| Walk-Forward 設計 | ✅ 有（`walkforward.py`：`hist = df.iloc[:ti+1]`，僅用 ≤ t 資料） |
| Out-of-Sample 設計 | ✅ 有（第 t 期選股，評估 t+1…t+HOLD） |
| 交易成本模型 | ✅ 有（`ml/costs.py`：手續費 0.1425%×2 + 證交稅 0.3% + 滑價） |
| 基準比較 | ✅ 有（隨機 / 等權 / 0050.TW 買進持有） |
| **是否曾實際執行** | ❌ **NO** — `data/backtests/` 不存在，**零產出** |

**結論：有回測程式 ≠ 已完成回測驗證。** 目前尚無任何回測結果。

執行方式（需可連網環境）：
```bash
python main.py --mode backtest
```

---

## Virtual Decision Panel 狀態

# **Architecture Only — NOT IMPLEMENTED**

| 項目 | 狀態 |
|---|---|
| 是否有 Panel 相關 Python 程式 | ❌ **無**（全 repo 搜尋無任何 Panel 決策程式） |
| 是否參與每日選股決策 | ❌ **NO** |
| 是否影響推播內容 | ❌ **NO** |

**Virtual Decision Panel 是「工程治理層」，不是產品功能。** 它的三個角色
（Architecture Reviewer / QA Reviewer / Release Risk Reviewer）
僅用於審查是否可推進下一階段，**不參與股票分析、不產生訊號、不影響任何交易邏輯**。

> 註：`ml/backtest_engine.py` 與 `ml/walkforward.py` 中的 `panel` 變數
> 指的是**價格面板（price panel）資料結構**，與 Virtual Decision Panel **無關**。

**目前 Panel 決策基準**：**NO-GO**（Gate Decision v2, APPROVED）
理由：① ML 未投入 Production ② 樣本不足 ③ 資料品質問題

---

## 工程治理狀態（Governance Status）

本專案採 Gate 制工程治理：

| 文件 | 狀態 |
|---|---|
| Virtual Decision Panel Gate Decision v2 | ✅ APPROVED — Decision: **NO-GO**（Baseline，不可變） |
| EDR-001（資料品質治理） | ✅ APPROVED WITH CONDITIONS（Option D） |
| Gate-A Implementation Plan v1.1 | ✅ APPROVED |
| **Gate-A Code 部署** | ✅ **完成** |
| **Gate-A 資料清理（CP2）** | ⏸ **Pending 核准** |

**Unlock Conditions（解除 NO-GO 所需）**：
- **U1** 資料品質達可信標準
- **U2** ML 模型成功訓練並完成至少一次 Production inference cycle
- **U3** 樣本具備決策效力（完成具統計代表性的 Alpha Evaluation）

---

## 已知限制（Current Limitations）

1. **ML 未上線** — `model.pkl` 不存在，每日決策 100% 為規則式。
2. **樣本不足** — 有標籤樣本 19 筆，Wilson 95% CI 為 [31.7%, 72.7%]，**橫跨 50%**，
   二項檢定 p ≈ 1.000 → **與隨機無法區分**。
3. **資料未清理** — `history.csv` 含 18.8% 髒資料（CP2 待核准）。
4. **回測零產出** — 引擎存在但從未執行。
5. **入場價偏樂觀** — 基準價為「前一日收盤」，實際須隔日開盤買入，存在**跳空缺口**，
   驗證績效可能偏樂觀。
6. **國定假日未排除** — Trading Day Guard 目前僅判斷週末；台股國定假日仍會觸發。
7. **零測試檔** — 專案無單元測試。
8. **處置股/停牌未排除** — 來源未標記，屬已知風險。

---

## 今天能證明什麼（What This Project Can Prove Today）

✅ **可以證明的**：

1. 系統每個交易日 **09:00 ±15 分鐘內**準時執行並推播（連續 5 交易日實測 ±3 分）。
2. 推播管線可靠（Telegram HTTP 200 + `ok=true` 才算成功；retry 機制）。
3. 非交易日不會執行、不會污染資料（Guard 已驗證）。
4. 資料品質問題可被自動偵測（Validator 已驗證）。
5. 不合格資料不會進入模型訓練（Training Gate 已驗證）。
6. 系統可持續累積預測與驗證資料。

---

## 今天還不能證明什麼（What It Cannot Prove Yet）

❌ **目前無法證明的**：

| 問題 | 現況 |
|---|---|
| 預測命中率是多少？ | **未知** — 19 筆樣本無統計效力（CI 橫跨 50%） |
| 策略是否具 Alpha？ | **未知** — 回測從未執行 |
| ML 模型是否有效？ | **未知** — 模型從未訓練 |
| 能否穩定賺取價差？ | **無證據** — 缺勝率、報酬、最大回撤、Sharpe、扣成本後對 0050 的超額報酬 |

**證明這些所需的條件**：
1. 完成資料清理（CP2）
2. 有標籤樣本達訓練門檻（≥ 30）→ 模型首次訓練 → 投入 Production
3. 累積足以具統計效力的樣本
4. 實際執行 walk-forward 回測，扣除交易成本，與 0050 基準比較

---

## 待辦事項（Pending Items）

| # | 項目 | 狀態 |
|---|---|---|
| 1 | **CP2 — 資料清理核准** | ⏸ 待核准 |
| 2 | **Data Cleanup**（`history.csv` 64 → 52 列） | ⏸ 待 CP2 |
| 3 | **ML Production**（首次訓練 + 上線） | ⏸ 待資料清理 + 樣本達 30 |
| 4 | **Virtual Decision Panel** | ⛔ NO-GO Baseline，且 Architecture Only |
| 5 | **Alpha Validation** | ⏸ 待回測執行 |
| 6 | **Walk-Forward 實際執行** | ⏸ 引擎存在，零產出 |

---

## 執行模式

| MODE | 觸發 | 說明 |
|---|---|---|
| `morning` | 09:00（週一~五） | 掃描 → 評分 → 推播 TOP 5 |
| `verify` | 14:45（週一~四） | 驗證已滿 5 交易日之預測，回填標籤 |
| `weekly` | 週五 20:00 | 當日驗證 + 週報 + ML 重訓（**目前被 Training Gate 擋下**） |
| `test` | 手動 | 推播測試訊息 |
| `backtest` | 手動 | 離線回測（**尚未執行過**） |

---

## 檔案結構

```
main.py                 MODE 分派 + Trading Day Guard
scheduler.py            MODE 解析唯一來源
config.py               常數 / 門檻 / 路徑
data_validator.py       資料品質檢查（唯讀）           ← Gate-A
core/
  scanner.py            TWSE + TPEx 候選掃描
  filter.py             技術特徵與濾網
  scorer.py             62 日勝率評分（目前決策核心）
  verifier.py           5 日波段標記 + 回填
  market_data.py        yfinance 包裝
  universe.py           回測用 universe
ml/
  ml_model.py           模型載入 + 預測（無模型 → None）
  trainer.py            RandomForest 重訓 + Training Gate  ← Gate-A
  backtest_engine.py    離線回測引擎（尚未執行）
  walkforward.py        walk-forward 邏輯（防未來洩漏）
  costs.py              台股交易成本模型
push/
  formatter.py          推播格式唯一定義
  telegram.py           Telegram（200 + ok=true 才算成功）
  line.py               LINE
storage/
  db.py                 db.json 讀寫
  history.py            history.csv（含去重）           ← Gate-A
  git_sync.py           Actions 內 commit 回 repo
scripts/
  clean_history.py      一次性清理（Dry Run，須核准）   ← Gate-A
.github/workflows/stock.yml
```

---

## 環境設定

| Secret | 說明 |
|---|---|
| `TG_TOKEN` / `TG_CHAT` | Telegram Bot |
| `LINE_TOKEN` / `LINE_ID` | LINE Messaging API |

**Settings → Actions → Workflow permissions** 須為 **Read and write**（供 git_sync 回寫）。

準時觸發需外部排程器（Google Apps Script）打 `repository_dispatch`，
event_type：`morning_run` / `verify_run` / `weekly_run`。

---

## 免責聲明

本系統為**研究型專案**，選股結果**不構成投資建議**。

**在完成資料治理、模型訓練、walk-forward 回測並證明風險調整後報酬為正之前，
本系統的任何輸出不應作為真實資金的交易依據。**

歷史統計不保證未來績效。投資有風險，請自行評估並承擔後果。
