# -*- coding: utf-8 -*-
"""Technical Analyst — 只用候選股現有真實欄位（rsi/ma20_diff/vx/chg/hi_lo_pos）。"""

from analyst.models import analyst_result

NAME = "technical"


def analyze(feat: dict) -> dict:
    rsi = feat.get("rsi")
    ma = feat.get("ma20_diff")
    vx = feat.get("vx")
    hlp = feat.get("hi_lo_pos")

    score = 50.0
    reasons, used = [], []

    if ma is not None:
        used.append("ma20_diff")
        if ma > 0:
            score += 15; reasons.append("站上MA20（多頭趨勢）")
        else:
            score -= 10; reasons.append("跌破MA20（趨勢偏弱）")

    if rsi is not None:
        used.append("rsi")
        if 50 <= rsi <= 70:
            score += 12; reasons.append(f"RSI {rsi:.0f} 健康偏強")
        elif rsi > 80:
            score -= 15; reasons.append(f"RSI {rsi:.0f} 過熱")
        elif rsi < 30:
            score += 5; reasons.append(f"RSI {rsi:.0f} 超賣（可能反彈）")

    if vx is not None:
        used.append("vx")
        if 1.2 <= vx <= 3:
            score += 10; reasons.append(f"量能溫和放大（{vx:.1f}倍）")
        elif vx > 5:
            score -= 8; reasons.append(f"爆量（{vx:.1f}倍，追高風險）")

    if hlp is not None:
        used.append("hi_lo_pos")
        if hlp >= 0.7:
            score += 6; reasons.append("收盤位於K棒高位（強勢）")

    score = max(0, min(100, score))
    verdict = "BUY" if score >= 65 else ("REJECT" if score < 40 else "WATCH")
    return analyst_result(NAME, round(score, 1), verdict, reasons, used)
