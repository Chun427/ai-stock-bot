# Gate Rules

## 核心規則
1. 任一 Reviewer FAIL → **立即停止**，不得修改任何程式。
2. 全部 PASS 才能進入下一關。
3. Senior Engineer **不得自行 merge** — 必經 GPT Supervisor 核准。
4. 未經 GPT Supervisor Approve，不得修改正式程式碼。
5. 每一關判定需附證據（檔案:行號 / 執行輸出）。無證據視為 FAIL。
6. 凍結區（見 FreezeList）非經雙 Reviewer 同缺陷，不得觸碰。

## 與其他規範的關係
- 變更範圍 → 見 `ChangeClassification.md`
- 風險等級 → 見 `RiskMatrix.md`
- 回歸項目 → 見 `RegressionMatrix.md`
- 凍結清單 → 見 `FreezeList.md`
- 模組層級 → 見 `ProjectScope.md`

## Applicable Repository
ai-stock-bot（唯一）
