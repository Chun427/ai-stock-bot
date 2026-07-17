# ADR-001: AI Analyst Panel

**狀態**: Accepted ｜ **日期**: 2026-07-16 ｜ **範圍**: ai-stock-bot

## 背景
原系統為「篩選 → 評分 → 推播」。使用者需求：篩選出的候選股，應經過
「AI 分析師會議討論後」再形成推薦，而非直接推播。

## 決策與理由

### 為什麼加入 Analyst Panel
將單一評分升級為多角色審查，讓推薦附帶「技術面 / 風險面」的判斷依據，
更接近投資研究流程。

### 為什麼 Fundamental SKIPPED
repo 目前無財報資料（EPS/PE/營收）。依 Governance「不捏造」原則，
無資料即不評分，標記 SKIPPED，絕不生成假財報分析。等未來接入資料再啟用。

### 為什麼 Consensus 不直接相信單一分析師
避免單一角度誤導。採「風險否決權」：Risk 判 REJECT 可否決 BUY，
寧可錯過不可錯買。

### 為什麼加入 Moderator
分離「投票彙整」與「會議結論產出」職責，便於未來擴充分析師，
不需重寫 consensus。

### 為什麼第一版不進推播
formatter 屬 Production Freeze。第一版 Panel 只寫 data/panel/json，
先驗證邏輯價值，不冒險動推播。

### 為什麼開關預設 False
`MORNING_SHOW_PANEL=False` 讓功能上線但推播不變，確認安全後才切 True。
出問題只需關開關，無需回退 commit。

## 後果
- 正面：可治理、可追溯、可關閉、不破壞原系統。
- 限制：第一版只有 Technical + Risk 兩位有效分析師。
- 待驗證：panel.review() 對 feat 欄位的相依（部署後確認）。
