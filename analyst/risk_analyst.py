# -*- coding: utf-8 -*-
"""Risk Analyst — 只用價量與風報比。明確聲明不含籌碼/事件/財報。"""

from analyst.models import analyst_result

NAME = "risk"
LIMIT_NOTE = "僅基於量價與風報比，未含籌碼、法人、新聞、事件風險"


def analyze(feat: dict, sc: dict, volatility=None) -> dict:
    """volatility: 若 panel 有算價格波動率則傳入；無則以量價間接評估。"""
    vx = feat.get("vx")
    chg = feat.get("chg")
    pred_gain = sc.get("pred_gain")

    score = 60.0  # 分數越高越安全
    reasons, risks, used = [], [], []

    # 風報比：pred_gain vs 停損 1.5%
    if pred_gain is not None:
        used.append("pred_gain")
        rr = pred_gain / 1.5
        if rr >= 2:
            score += 12; reasons.append(f"風報比佳（約{rr:.1f}）")
        elif rr < 1:
            score -= 12; risks.append(f"風報比偏低（約{rr:.1f}）")

    # 過熱風險
    if vx is not None and chg is not None:
        used += ["vx", "chg"]
        if vx > 4 and chg > 5:
            score -= 15; risks.append("爆量大漲，短線過熱")
        elif chg > 8:
            score -= 10; risks.append(f"單日漲幅{chg:.1f}%，追高風險")

    if volatility is not None:
        used.append("volatility")
        if volatility > 0.05:
            score -= 10; risks.append(f"近期波動偏高（{volatility*100:.1f}%）")

    score = max(0, min(100, score))
    verdict = "BUY" if score >= 65 else ("REJECT" if score < 40 else "WATCH")
    r = analyst_result(NAME, round(score, 1), verdict, reasons, used, note=LIMIT_NOTE)
    r["risks"] = risks
    return r
