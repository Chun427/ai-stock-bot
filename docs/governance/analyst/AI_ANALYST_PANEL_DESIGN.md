# AI Analyst Panel — 總體設計

## 定位
Business Feature（**非** Engineering Governance Reviewer）。
候選股完成 `scorer` / `ranking` 後，進入三位 AI 股票分析師討論，產生 Consensus。

> ⚠️ 與 Engineering Governance 的三位 Reviewer（Architecture / QA / Senior Engineer）**完全無關**，
> 那三位審查程式碼品質，本 Panel 分析股票。兩系統不得混用。

## 三位分析師（第一版狀態）

| 分析師 | 狀態 | 資料來源 |
|---|---|---|
| ① Technical Analyst | ✅ **啟用** | rsi / ma20_diff / vx / chg（現有真實資料） |
| ② Risk Analyst | ✅ **啟用** | 由價量歷史算波動 + 風報比（現有資料） |
| ③ Fundamental Analyst | ⏸ **SKIPPED（保留 interface，第一版不評分）** | 無財報資料源 → 不捏造 |

## 資料流插入點

```
scanner → filter → scorer → ranking TOP_N
                                 ↓
                    ★ panel.review(candidates) ★   ← 只讀候選、只加欄位
                                 ↓
                          formatter → push
```

- Panel **只讀** candidate，**只附加** `analyst_panel` 欄位，不改任何原欄位。
- 第一版：Panel 結果寫獨立輸出（`data/panel/`），**不進推播**（不動 formatter）。
- 未來若要在推播顯示 consensus → 需另外批准修改 formatter（凍結區）。

## 輸出資料結構

```json
{
  "stock": "5434",
  "analyst_votes": {
    "technical":   { "score": 72, "verdict": "BUY",  "reasons": [...] },
    "risk":        { "score": 55, "verdict": "WATCH","reasons": [...] },
    "fundamental": { "score": null, "verdict": "SKIPPED", "note": "財報資料未接入" }
  },
  "consensus": "WATCH",
  "confidence": 0.63,
  "effective_analysts": ["technical", "risk"],
  "reasons": [...],
  "risks": [...]
}
```

## 不捏造原則（最高約束）
- 無資料的分析師一律標 `SKIPPED` / `DATA_UNAVAILABLE`，**不得生成假分析**。
- Consensus 只由**有效分析師**計算，並註明依據哪幾面。
- 任何評分都必須可回溯到真實欄位。

## 分階段
```
Phase 1 Architecture   ✅ 完成
Phase 2 設計文件        ← 現在
Phase 3 新增 module
Phase 4 測試
Phase 5 正式整合
每次進入前：Architecture PASS + QA PASS + GPT Approve
```
