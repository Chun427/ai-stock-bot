# Consensus Rules

## 原則
Consensus **只由有效分析師（有資料、非 SKIPPED）計算**。

## 第一版有效分析師
- Technical（啟用）
- Risk（啟用）
- Fundamental → SKIPPED，不計入

## 投票與共識
每位有效分析師輸出 verdict ∈ {BUY, WATCH, REJECT}。

| 情境 | Consensus |
|---|---|
| 全部 BUY | BUY |
| 有 REJECT | 最保守優先 → 至少 WATCH，若風險判 REJECT 則 REJECT |
| 混合 BUY/WATCH | WATCH |
| Risk = REJECT | 直接 REJECT（風險否決權） |

> 設計原則：**風險優先**。Risk Analyst 對 REJECT 有否決權，寧可錯過不可錯買。

## Confidence（信心度）
```
confidence = 有效分析師一致程度 × 資料完整度折扣
```
- 第一版只有 2 位有效 → 資料完整度折扣（因 Fundamental 缺席）
- 明確標示 confidence 已因基本面缺席而下修

## 輸出必附
- `effective_analysts`: 實際參與的分析師清單
- `consensus_basis`: 「基於技術面與風險面（基本面資料缺失）」

## 不捏造
- 只有 2 位分析師時，**不得假裝三方共識**。
- confidence 不得虛高；缺資料必須反映在信心度下修。
