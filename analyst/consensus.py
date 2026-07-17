# -*- coding: utf-8 -*-
"""Consensus — 只彙整有效分析師（非 SKIPPED）。風險否決權。不重新分析。"""


def compute(results: list) -> dict:
    """輸入 AnalystResult list，回傳共識摘要（不含會議文字，那是 Moderator 的事）。"""
    active = [r for r in results if r["status"] == "ACTIVE" and r["score"] is not None]
    skipped = [r["analyst"] for r in results if r["status"] == "SKIPPED"]

    if not active:
        return {"consensus": "WATCH", "confidence": 0.0,
                "effective": [], "skipped": skipped,
                "votes": {r["analyst"]: r["verdict"] for r in results}}

    votes = {r["analyst"]: r["verdict"] for r in active}

    # 風險否決權：risk 判 REJECT → 直接 REJECT
    risk = next((r for r in active if r["analyst"] == "risk"), None)
    if risk and risk["verdict"] == "REJECT":
        consensus = "REJECT"
    elif any(r["verdict"] == "REJECT" for r in active):
        consensus = "WATCH"  # 有人 REJECT 但非 risk → 至少保守
    elif all(r["verdict"] == "BUY" for r in active):
        consensus = "BUY"
    else:
        consensus = "WATCH"

    # 信心度：一致程度 × 資料完整度折扣（缺席者越多折扣越大）
    agree = sum(1 for r in active if r["verdict"] == consensus) / len(active)
    completeness = len(active) / (len(active) + len(skipped))
    confidence = agree * completeness

    return {"consensus": consensus, "confidence": confidence,
            "effective": [r["analyst"] for r in active],
            "skipped": skipped, "votes": votes}
