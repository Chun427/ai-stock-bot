# README 更新說明（AI Analyst Panel v1.0）

> 將 README「系統架構」與「每日執行流程」相關段落更新如下。

## 更新後的架構圖

```
repository_dispatch  →  GitHub Actions（stock.yml）
        │
        ▼
   scanner → filter → scorer → ranking TOP_N
        │
        ▼
   ┌──────────────────────────────┐
   │  AI Analyst Panel（v1.0）     │
   │   ├── Technical Analyst  ✅   │
   │   ├── Risk Analyst       ✅   │
   │   ├── Fundamental Analyst ⏸ SKIPPED │
   │   ├── Moderator（彙整）        │
   │   └── Consensus（風險否決權）  │
   └──────────────────────────────┘
        │  （寫 data/panel/*.json；開關 MORNING_SHOW_PANEL）
        ▼
   push/formatter → Telegram + LINE
```

## 每日執行流程表更正

| 步驟 | 原內容 | 更新為 |
|---|---|---|
| 7 Virtual Decision Panel | ❌ NOT IMPLEMENTED | ✅ **AI Analyst Panel 已實作**（Technical + Risk；Fundamental SKIPPED；寫 data/panel/，開關預設 False 不進推播） |

## 補充說明
- Panel 為附加層，**不改** scanner/filter/scorer 既有邏輯。
- 開關 `MORNING_SHOW_PANEL`（push/formatter.py）預設 False：推播與舊版一致。
- 詳見 `docs/analyst/`（設計）與 `docs/governance/adr/ADR-001`（決策紀錄）。
