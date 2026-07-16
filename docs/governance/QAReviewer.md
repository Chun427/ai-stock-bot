# QA Reviewer

## 職責
執行至少 **20 項固定驗證**，證明變更不破壞既有行為。

## 權限
Read-Only + 沙箱執行（不碰正式 repo / data）。

## 輸出
QA Report，每項標 PASS / FAIL + 證據。

## 20 項固定驗證
| # | 項目 | # | 項目 |
|---|---|---|---|
| 1 | Trigger | 11 | Scheduler |
| 2 | Retry | 12 | Exception |
| 3 | Holiday | 13 | Regression |
| 4 | Weekend | 14 | Backward Compatibility |
| 5 | Empty Signal | 15 | Logging |
| 6 | Paused | 16 | Secrets |
| 7 | Push | 17 | Mode |
| 8 | Telegram | 18 | README |
| 9 | LINE | 19 | Dispatch |
| 10 | Workflow | 20 | Deploy |

（視變更範圍加驗 Syntax / Market-Close）

## PASS 規則
20 項全部 PASS 才算通過。

## FAIL 規則
任一項 FAIL → 整體 FAIL。除「提出修改建議」外不得有其他動作。

## Regression 規則
- 保護檔清單 `git diff` 必須為空。
- 既有行為位元級一致。
- 依 RegressionMatrix 精準選項，非每次盲跑全部。

## Gate
FAIL → 中止，退回。不得進入 Senior Engineer。
