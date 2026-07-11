# AI Stock Bot — Push Hardening

Version: Production Hardened Notification Layer

## Changes
- Telegram 成功判定強化：由「HTTP 200」升級為「HTTP 200 + response JSON `ok=true`」
- 避免 Telegram 回 200 但 `{"ok":false}` 被誤判為成功（false success）
- 保留既有 retry ×4（指數退避）、timeout、fail-safe、logging

## Not Changed
- AI model / scanner / scorer / filter（選股核心）
- formatter（推播格式）
- push/line.py（LINE 推播）
- scheduler.py / workflow / GAS trigger
- main.py / config.py

## Scope
本次僅修改 `push/telegram.py` 的成功判定邏輯，屬 Notification Reliability，
不影響任何業務邏輯與 AI 流程。單檔可覆蓋、可快速回滾。

## Verification
- V1 Syntax: `python -m py_compile push/telegram.py` → PASS
- Behavior:
  - HTTP 200 + ok=true   → success
  - HTTP 200 + ok=false  → fail（重試後）
  - HTTP 200 + 非 JSON   → fail
- Runtime: 待 GAS `testNow` 端到端確認（手機收到）
