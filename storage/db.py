# -*- coding: utf-8 -*-
"""
storage/db.py
db.json 讀寫。
結構：{ "PRED_YYYY-MM-DD": {date, spy, qqq, scanner, stocks:[...], verified:bool, ...} }
- 損毀自動重建為空物件
- 寫入失敗回傳 False（呼叫端記入 REPORT，流程繼續）
"""

import os
import json

import config
from utils.logger import get_logger

log = get_logger("db")


def load() -> dict:
    if not os.path.exists(config.DB_PATH):
        log.info("db.json 不存在，視為空")
        return {}
    try:
        with open(config.DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("db.json 根節點非物件")
        return data
    except Exception as e:  # noqa: BLE001
        log.error(f"db.json 損毀（{e}），自動重建為空物件")
        return {}


def save(data: dict) -> bool:
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        tmp = config.DB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, config.DB_PATH)  # 原子寫入
        return True
    except Exception as e:  # noqa: BLE001
        log.error(f"db.json 寫入失敗：{e}")
        return False


def key_for(date_str: str) -> str:
    return f"PRED_{date_str}"
