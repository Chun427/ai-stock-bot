# AI Analyst Panel v1.0 — Deployment Checklist

## 上傳階段
- [ ] `analyst/` 已新增（9 檔）
- [ ] `docs/analyst/` 已新增（設計文件）
- [ ] `main.py` 已更新（Panel 整合 + push_stocks optional 欄位）
- [ ] `push/formatter.py` 已更新（MORNING_SHOW_PANEL 開關 + 會議行）
- [ ] `MORNING_SHOW_PANEL = False`（確認預設關閉）

## 首次執行驗證（開關 False）
- [ ] GitHub Actions morning 成功執行
- [ ] `data/panel/YYYY-MM-DD.json` 已產生   ← ★ 最重要，證明 Panel 真的在跑
- [ ] `REPORT["panel"] == "success"`（非 fail，非靜默失敗）
- [ ] Telegram 推播正常收到
- [ ] 推播內容與舊版一致（無會議行，因開關 False）
- [ ] 無 exception（Actions log 無 error）

## Panel 內容合理性（讀 json 檢查）
- [ ] consensus 值合理（BUY/WATCH/REJECT）
- [ ] confidence 有數值（因 fundamental 缺席應 < 1.0）
- [ ] fundamental 為 SKIPPED，未參與投票
- [ ] technical/risk 的 reasons 可回溯到真實欄位

## 連續觀察（三個交易日）
- [ ] Day 1：json 正常 + 推播正常
- [ ] Day 2：json 正常 + 推播正常
- [ ] Day 3：json 正常 + 推播正常

## 批准切換（三日無誤後）
- [ ] GPT Supervisor 批准
- [ ] `MORNING_SHOW_PANEL = True`
- [ ] 次日推播出現「🧑‍💼 分析師會議：...」
- [ ] 推播格式正常、未過長

## Rollback（任何異常）
- [ ] `MORNING_SHOW_PANEL = False` → 推播即恢復原狀（無需回退 commit）
