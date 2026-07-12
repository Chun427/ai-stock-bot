# CHANGELOG

## [Performance Metric Alignment] — 績效計算與交易規則對齊

### 問題（Root Cause）
`core/verifier.py` 的**成功判定**假設「觸 +3% 停利 / 觸 −1.5% 停損」即出場，
但 **`actual_pct` 一律以第 5 日收盤價計算**，造成策略規則與績效統計為兩套邏輯。

實際出現的矛盾（真實資料）：
```
彩晶 6116   判定 ✅命中，但記錄報酬 −6.43%
同欣電 6271 判定 ✅命中，但記錄報酬 −7.49%
美利達 9914 判定 ✅命中，但記錄報酬 −2.67%
```
若持續累積，Dashboard 與後續策略比較將建立在錯誤數字上。

### Changed
- `core/verifier.py` → `_label_and_actual()`：`actual_pct` 依**實際出場方式**計算
  1. 先觸停利（High ≥ +3%）→ `actual_pct = +3.0%`
  2. 先觸停損（Low ≤ −1.5%）→ `actual_pct = −1.5%`
  3. 5 日內皆未觸發 → `actual_pct = 第 5 日收盤` 相對買價
  - 停損優先於停利（同日先檢查 Low，與原邏輯一致）

### Unchanged（本次全部凍結）
- 交易門檻：`HIT_THRESHOLD=+3%`、`STOP_THRESHOLD=−1.5%`、`VERIFY_WINDOW=5`
- `label` 判定邏輯（命中率不變，仍為既有基準）
- scanner / feature engineering / RandomForest / scorer / 排名邏輯
- formatter（推播格式）/ workflow / scheduler / GAS / push

### 重要說明（措辭）
本次**不是策略優化、不是提高收益、不是調模型**。
> 績效計算方式與既有交易規則一致，因此 KPI 更能反映策略實際執行結果。

以前：錯誤記帳；現在：正確記帳。**策略本身沒有變強。**

### 影響面
`actual_pct` 僅由 `verifier` 產生、`formatter.verify` 顯示；
**不寫入 `history.csv`、不進入 ML 訓練**（訓練僅使用 `target_label`）→ 模型零污染。
