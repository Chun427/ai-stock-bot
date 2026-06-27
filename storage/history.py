# -*- coding: utf-8 -*-
"""
storage/history.py
history.csv 讀寫（ML 訓練來源）。
欄位：config.HISTORY_HEADER
- 不存在自動建立含標頭空檔
- append 特徵列（target_label 初值留空）
- 驗證後回填 target_label
使用標準庫 csv，避免在純寫入時硬依賴 pandas。
"""

import os
import csv

import config
from utils.logger import get_logger

log = get_logger("history")


def _ensure():
    if not os.path.exists(config.HISTORY_PATH):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(config.HISTORY_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(config.HISTORY_HEADER)
        log.info("history.csv 不存在，已建立含標頭空檔")


def append_features(rows: list) -> bool:
    """rows: list[dict]，key 對應 HISTORY_HEADER（target_label 可省略=空）。"""
    try:
        _ensure()
        with open(config.HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=config.HISTORY_HEADER)
            for r in rows:
                w.writerow({k: r.get(k, "") for k in config.HISTORY_HEADER})
        return True
    except Exception as e:  # noqa: BLE001
        log.error(f"history.csv 寫入失敗：{e}")
        return False


def read_all() -> list:
    _ensure()
    try:
        with open(config.HISTORY_PATH, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception as e:  # noqa: BLE001
        log.error(f"history.csv 讀取失敗：{e}")
        return []


def backfill_label(date: str, code: str, label: int) -> bool:
    """以 (date, code) 為鍵回填 target_label。"""
    try:
        rows = read_all()
        changed = False
        for r in rows:
            if r.get("date") == date and r.get("code") == str(code):
                r["target_label"] = str(label)
                changed = True
        if not changed:
            log.warning(f"未找到可回填列 date={date} code={code}")
            return False
        with open(config.HISTORY_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=config.HISTORY_HEADER)
            w.writeheader()
            w.writerows(rows)
        return True
    except Exception as e:  # noqa: BLE001
        log.error(f"target_label 回填失敗：{e}")
        return False


def labeled_count() -> int:
    return sum(1 for r in read_all() if str(r.get("target_label", "")).strip() in ("0", "1"))
