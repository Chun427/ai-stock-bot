# -*- coding: utf-8 -*-
"""AI Analyst Panel 主控。candidate → 三分析師 → Moderator → Consensus。

只讀候選股、只回傳結論物件，不改任何既有欄位、不寫推播。
"""

from analyst import technical_analyst, risk_analyst, fundamental_analyst
from analyst import consensus as consensus_mod
from analyst import moderator
from analyst.models import consensus_result


def review_one(name, code, feat: dict, sc: dict, volatility=None) -> dict:
    """對單一候選股跑完整 Panel，回傳 ConsensusResult。"""
    results = [
        technical_analyst.analyze(feat),
        risk_analyst.analyze(feat, sc, volatility),
        fundamental_analyst.analyze(feat),
    ]
    cons = consensus_mod.compute(results)
    summary = moderator.summarize(results, cons)

    return consensus_result(
        stock=code,
        consensus=cons["consensus"],
        confidence=cons["confidence"],
        effective=cons["effective"],
        skipped=cons["skipped"],
        votes={r["analyst"]: {"score": r["score"], "verdict": r["verdict"]} for r in results},
        reasons=summary["reasons"],
        risks=summary["risks"],
        basis=summary["consensus_basis"],
    )


def review(top: list) -> dict:
    """對 ranking 後的 top list 全部跑 Panel。回傳 {code: ConsensusResult}。"""
    out = {}
    for t in top:
        feat, sc = t["feat"], t["sc"]
        out[t["code"]] = review_one(t["name"], t["code"], feat, sc)
    return out
