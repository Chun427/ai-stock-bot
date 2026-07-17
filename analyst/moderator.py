# -*- coding: utf-8 -*-
"""Moderator — 純彙整器。不分析、不投票、不產生新資料，只重組分析師意見為會議結論。"""


def summarize(results: list, consensus: dict) -> dict:
    """把各分析師的 reasons/risks 彙整成會議結論文字。"""
    reasons, risks = [], []
    for r in results:
        if r["status"] != "ACTIVE":
            continue
        for x in r.get("reasons", []):
            reasons.append(f"[{r['analyst']}] {x}")
        for x in r.get("risks", []):
            risks.append(f"[{r['analyst']}] {x}")

    n_active = len(consensus["effective"])
    n_skip = len(consensus["skipped"])
    basis = f"本次共識基於{n_active}位分析師（{', '.join(consensus['effective'])}）"
    if n_skip:
        basis += f"；{', '.join(consensus['skipped'])} 因資料未接入而未參與"
    basis += "。基本面資料尚未接入。"

    return {"reasons": reasons, "risks": risks, "consensus_basis": basis}
