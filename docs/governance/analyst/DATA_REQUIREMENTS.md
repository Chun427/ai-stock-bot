# Data Requirements

## 現有資料（候選股 Data Contract）
```
name, code, price, winrate, pred_gain, n_signals, weight, score,
rsi, vx, chg, ma20_diff, hi_lo_pos
```
來源：yfinance OHLCV（`core/market_data.py`）。

## 各分析師資料需求對照

| 分析師 | 需要 | 現況 | 缺口 |
|---|---|---|---|
| Technical | rsi/ma/量/動能 | ✅ 有（缺 MACD） | MACD（可由價格加算） |
| Risk | 波動/風報比 | ⚠️ 可由現有算 | 籌碼、事件（無源） |
| Fundamental | EPS/營收/PE/PB | ❌ 全缺 | 需接財報資料源 |

## 未來資料接入計畫（非本階段執行）
| 資料 | 候選來源 | 影響 |
|---|---|---|
| EPS/營收/PE | yfinance `.info`/`.financials`、公開資訊觀測站 | 需新增抓取模組（獨立，不動現有） |
| 波動率 | 現有價格歷史計算 | 純加法 |
| MACD | 現有價格歷史計算 | 純加法 |
| 籌碼/事件 | 第三方 API | 較大工程，另評估 |

## 原則
- 接任何新資料源 = 新增獨立模組，**不改** scanner/scorer/filter。
- 資料未到位前，對應分析師一律 SKIPPED，不捏造。
