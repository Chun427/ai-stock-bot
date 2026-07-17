# -*- coding: utf-8 -*-
"""檢查候選股有哪些欄位可用，決定各分析師啟用或 SKIP。不評分、不捏造。"""

TECHNICAL_FIELDS = ["rsi", "ma20_diff", "vx", "chg", "hi_lo_pos"]
RISK_FIELDS = ["vx", "chg"]          # 波動由價格歷史另計；此為候選股內可得欄位
FUNDAMENTAL_FIELDS = ["eps", "pe", "revenue"]  # 目前一定缺


def check(feat: dict) -> dict:
    """回傳每個分析師的資料可用性。"""
    def avail(fields):
        return [f for f in fields if f in feat and feat.get(f) is not None]

    tech = avail(TECHNICAL_FIELDS)
    risk = avail(RISK_FIELDS)
    fund = avail(FUNDAMENTAL_FIELDS)
    return {
        "technical": {"available": tech, "ok": len(tech) >= 3},
        "risk": {"available": risk, "ok": len(risk) >= 1},
        "fundamental": {"available": fund, "ok": len(fund) >= 1},  # 恆 False
    }
