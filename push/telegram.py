# -*- coding: utf-8 -*-
"""
push/telegram.py
Telegram Bot 推播。
- 訊息超過 4096 字元自動截斷
- retry × 4（指數退避）
- 回傳 'success' / 'fail' / 'not_configured'
- 任何例外皆攔截，不向外丟出（fail-safe）
"""

import time
import requests

import config
from utils.logger import get_logger

log = get_logger("telegram")
API = "https://api.telegram.org/bot{token}/sendMessage"


def _truncate(text: str) -> str:
    if len(text) <= config.TG_MAX_LEN:
        return text
    log.warning(f"訊息超過 {config.TG_MAX_LEN} 字元，自動截斷")
    return text[: config.TG_MAX_LEN - 20] + "\n…（訊息已截斷）"


def push(text: str) -> str:
    if not config.TG_TOKEN or not config.TG_CHAT:
        log.info("[TG] 未設定 TG_TOKEN/TG_CHAT，略過")
        return "not_configured"

    body = {"chat_id": config.TG_CHAT, "text": _truncate(text)}
    url = API.format(token=config.TG_TOKEN)

    for attempt in range(1, config.TG_RETRY + 1):
        try:
            r = requests.post(url, json=body, timeout=config.NET_TIMEOUT)
            log.info(f"[TG] HTTP {r.status_code} (attempt {attempt})")
            if r.status_code == 200:
                log.ok("[TG] 發送成功")
                return "success"
            log.warning(f"[TG] 非 200：{r.text[:160]}")
        except Exception as e:  # noqa: BLE001
            log.warning(f"[TG] 例外 attempt {attempt}: {e}")
        if attempt < config.TG_RETRY:
            time.sleep(2 ** attempt)  # 指數退避：2,4,8…

    log.error("[TG] 4 次重試後仍失敗")
    return "fail"
