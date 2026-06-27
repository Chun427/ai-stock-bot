# -*- coding: utf-8 -*-
"""
core/weekly_report.py
週報彙整：統計本週（最近 7 日）已驗證紀錄的命中率。
回傳 (hits, total)。
"""

from datetime import datetime, timedelta

from utils.logger import get_logger

log = get_logger("weekly_report")


def summarize(db: dict):
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    hits, total = 0, 0
    for key, rec in db.items():
        if not key.startswith("PRED_"):
            continue
        if not rec.get("verified"):
            continue
        if rec.get("date", "") < cutoff:
            continue
        for s in rec.get("stocks", []):
            lab = s.get("label")
            if lab is None:
                continue
            total += 1
            if lab == 1:
                hits += 1
    log.info(f"本週彙整：{hits}/{total}")
    return hits, total
