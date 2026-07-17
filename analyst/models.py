# -*- coding: utf-8 -*-
"""AI Analyst Panel — 資料結構（純結構，無業務邏輯）。"""


def analyst_result(analyst, score, verdict, reasons=None, data_used=None,
                   status="ACTIVE", note=""):
    """單一分析師輸出。score 為 None 代表未評分（如 SKIPPED）。"""
    return {
        "analyst": analyst,
        "status": status,          # ACTIVE / SKIPPED
        "score": score,            # 0-100 或 None
        "verdict": verdict,        # BUY / WATCH / REJECT / SKIPPED
        "reasons": reasons or [],
        "data_used": data_used or [],
        "note": note,
    }


def consensus_result(stock, consensus, confidence, effective, skipped,
                     votes, reasons, risks, basis):
    """Panel 對單一候選股的最終結論。"""
    return {
        "stock": stock,
        "consensus": consensus,            # BUY / WATCH / REJECT
        "confidence": round(confidence, 2),
        "effective_analysts": effective,
        "skipped_analysts": skipped,
        "votes": votes,
        "reasons": reasons,
        "risks": risks,
        "consensus_basis": basis,
    }
