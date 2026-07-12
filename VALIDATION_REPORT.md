# VALIDATION REPORT — Performance Metric Alignment

## 修改範圍
- **Modified**: `core/verifier.py`（僅 `_label_and_actual()` 的報酬計算）
- **Not Modified**: scanner / feature / scorer / RandomForest / ranking /
  formatter / workflow / scheduler / GAS / push / config 門檻

---

## 五輪驗證

### V1 — Syntax
`python -m py_compile core/verifier.py` → **PASS**

### V2 — 出場路徑（四情境實測，買價=100）
| 情境 | 結果 | 期望 | 判定 |
|---|---|---|---|
| 停利（第2日 High 104） | `(label=1, +3.0%)` | label=1, +3.0 | ✅ PASS |
| 停損（第2日 Low 98） | `(label=0, −1.5%)` | label=0, −1.5 | ✅ PASS |
| 時間出場（皆未觸發） | `(label=0, +1.2%)` | label=0, 第5日close | ✅ PASS |
| 停損優先（同日先觸停損） | `(label=0, −1.5%)` | label=0, −1.5 | ✅ PASS |

### V3 — label 不變（模型評價基準保護）
命中判定邏輯**一字未改**；19 筆已驗證樣本命中率維持 **10/19 = 52.6%**。 → **PASS**

### V4 — 影響面分析
`actual_pct` 消費者僅 `push/formatter.py`（顯示用）。
`history.csv` 僅存 `target_label`，ML 訓練不使用 `actual_pct`。
→ **模型零污染** → **PASS**

### V5 — Regression
| 元件 | 狀態 |
|---|---|
| AI Model (RandomForest) | PASS（未動） |
| Scanner / Feature / Scorer | PASS（未動） |
| Push / Formatter | PASS（未動） |
| Workflow / Scheduler / GAS | PASS（未動） |
| 交易門檻（+3% / −1.5% / 5日） | PASS（未動） |

---

## 新舊 KPI 比較（真實 19 筆已驗證樣本）

| 指標 | 舊（抱滿5日收盤） | 新（依規則出場） |
|---|---|---|
| 命中率 | 52.6% | **52.6%（不變）** |
| 平均報酬 | +0.29% | +1.20% |
| 中位數 | −1.73% | +3.00% |
| 最大獲利 | +52.13% | +3.00%（停利上限） |
| 最大虧損 | −22.46% | −1.50%（停損保護） |
| 正報酬比例 | 42.1% | 63.2% |

### 解讀（重要）
> **這不是策略變強，是記帳變正確。**
> 新數字為「若嚴格執行既有交易規則」之結果，與規則定義一致。

### 已知限制（誠實揭露）
1. 假設停利/停損可在觸價成交；真實交易存在滑價與跳空。
2. 入場價仍為「前一交易日收盤價」（樂觀偏誤未解，屬 Level 2，本次不碰）。
3. 樣本僅 19 筆、集中同一週市況，**不足以評斷模型優劣**。

---

## Production Status
**READY**（單檔可覆蓋、可快速回滾）
