# CHANGELOG

## [Push Hardening] — Telegram success validation

### Changed
- `push/telegram.py`: 成功判定由 `HTTP 200` 改為 `HTTP 200 AND response.json()["ok"] == True`。
  Telegram API 偶爾回 200 但 body `{"ok":false}`（例如 chat 被封鎖、參數錯誤），
  舊邏輯會誤判為成功；新邏輯正確判為失敗並觸發重試 / 回報 fail。

### Preserved
- retry ×4（指數退避 2/4/8s）
- timeout（NET_TIMEOUT）
- 4096 字元截斷
- fail-safe（例外不外拋）
- 回傳值語意：'success' / 'fail' / 'not_configured'

### Not Changed (Regression-protected)
- scanner / scorer / model / filter / formatter
- main.py / config.py / scheduler.py
- .github/workflows/stock.yml
- push/line.py
- GAS trigger.gs

### Reference
- 以 stock-notify-bot 的 `notify/telegram_notifier.py` 作為 Notification Reliability
  Benchmark，僅 Merge「response ok 驗證」此一項優化，未搬移其架構。

### Runtime Verification (pending)
- GAS `testNow` → repository_dispatch → Actions → main.py → Telegram → 手機通知
