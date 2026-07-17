# -*- coding: utf-8 -*-
"""Fundamental Analyst — 第一版 SKIPPED。無財報資料，絕不捏造。"""

from analyst.models import analyst_result

NAME = "fundamental"
REQUIRED = ["EPS", "營收", "本益比 PE", "股價淨值比 PB"]


def analyze(feat: dict) -> dict:
    """第一版恆回 SKIPPED。未來接入財報資料後才實作真實評分。"""
    return analyst_result(
        NAME, score=None, verdict="SKIPPED",
        reasons=[], data_used=[], status="SKIPPED",
        note="目前系統未接入財報資料，本項不評分。需要：" + ", ".join(REQUIRED),
    )
