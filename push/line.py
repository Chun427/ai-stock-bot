# -*- coding: utf-8 -*-
"""
push/line.py
LINE Messaging API 推播（push message）。
- retry × 3
- 回傳 'success' / 'fail' / 'not_configured'
- 任何例外皆攔截（fail-safe）
注意：LINE 單則 text 上限 5000 字元，這裡保守截斷至 4900。
"""

import time
import requests

import config
from utils.logger import get_logger

log = get_logger("line")
API = "https://api.line.me/v2/bot/message/push"
LINE_MAX_LEN = 4900


def _truncate(text: str) -> str:
    if len(text) <= LINE_MAX_LEN:
        return text
    log.warning("訊息過長，自動截斷")
    return text[: LINE_MAX_LEN - 20] + "\n…（訊息已截斷）"


def push(text: str) -> str:
    if not config.LINE_TOKEN or not config.LINE_ID:
        log.info("[LINE] 未設定 LINE_TOKEN/LINE_ID，略過")
        return "not_configured"

    headers = {
        "Authorization": f"Bearer {config.LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "to": config.LINE_ID,
        "messages": [{"type": "text", "text": _truncate(text)}],
    }

    for attempt in range(1, config.LINE_RETRY + 1):
        try:
            r = requests.post(API, headers=headers, json=body,
                              timeout=config.NET_TIMEOUT)
            log.info(f"[LINE] HTTP {r.status_code} (attempt {attempt})")
            if r.status_code == 200:
                log.ok("[LINE] 發送成功")
                return "success"
            # 429/5xx 可重試；其餘（如 400 額度用盡）直接失敗
            if r.status_code not in (429, 500, 502, 503):
                log.error(f"[LINE] 不可重試錯誤：{r.text[:160]}")
                return "fail"
            log.warning(f"[LINE] 可重試錯誤：{r.text[:160]}")
        except Exception as e:  # noqa: BLE001
            log.warning(f"[LINE] 例外 attempt {attempt}: {e}")
        if attempt < config.LINE_RETRY:
            time.sleep(2 ** attempt)

    log.error("[LINE] 3 次重試後仍失敗")
    return "fail"
