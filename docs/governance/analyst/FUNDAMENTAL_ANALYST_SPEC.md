# Fundamental Analyst — 規格（第一版 SKIPPED）

## 狀態
⏸ **SKIPPED**：保留 interface，第一版**不啟用評分**，等待 Financial Data Provider。

## 為什麼不啟用
repo 目前**完全沒有基本面資料**（無 EPS / 營收 / PE / 財報）。
依「不捏造」最高原則，無資料即**不得產出任何財報分析**。

## 第一版行為（固定輸出）
```json
{
  "score": null,
  "verdict": "SKIPPED",
  "note": "目前系統未接入財報資料，本項不評分",
  "required_data": ["EPS", "營收", "本益比 PE", "股價淨值比 PB"]
}
```
- **不參與** consensus 計算。
- **不生成**任何評語、推測、佔位分析。

## 未來啟用條件（Data Requirements）
| 需要資料 | 可能來源 |
|---|---|
| EPS / 營收 | 公開資訊觀測站、yfinance `.financials` |
| PE / PB | yfinance `.info` |
啟用需經：資料源接入 → Architecture PASS → QA PASS → GPT Approve。

## Interface（保留，供未來實作）
```
fundamental_analyst.analyze(stock) -> {score, verdict, reasons}
第一版恆回 SKIPPED；未來接資料後才回真實評分。
```
