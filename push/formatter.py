# -*- coding: utf-8 -*-
"""
push/formatter.py
==================
所有推播訊息的唯一定義處（OUTPUT CONTRACT / 不可變契約）。
任何格式調整只能改這裡，其他模組禁止自行拼字串。

⚠️ 契約決策開關（README 與使用者螢幕有 4 處歧異，集中於此，改一行即可）
   依使用者最終提供之螢幕為預設，待確認。
"""

# ─────────────────────────────────────────────────────────
# 🔧 CONTRACT TOGGLES（4 處歧異，確認後鎖定）
# ─────────────────────────────────────────────────────────
# #1 早盤標題：使用者螢幕="預測模式"；README="AI+Rule 混合模式"
HEADER_MORNING = "【AI 選股 - 預測模式】"
# #2 驗證報告是否加上下邊框（使用者螢幕=加）
VERIFY_TOP_BORDER = True
# #3 括號：使用者螢幕=半形 ()
LP, RP = "(", ")"
# #4 是否在訊息內含「【收盤驗證】」標題（使用者=否，視為區段標籤）
VERIFY_INNER_HEADER = ""   # 留空＝不含；若要顯示填 "【收盤驗證】"
# #5 ML 回測報告標題（GPT 監督更新：乾淨化，移除 TimeSeriesSplit 字樣）
HEADER_ML_BACKTEST = "【ML 回測報告】"
# #6 早盤是否顯示 ML 分數 🤖（GPT 鎖死版=不顯示；與更早的 🤖9.9 螢幕衝突，待確認）
MORNING_SHOW_ML = False
MORNING_SHOW_PANEL = False   # AI 分析師會議結論顯示開關（預設關閉，開關 False 時推播完全不變）
# ─────────────────────────────────────────────────────────

BAR = "━" * 14
RANK_EMOJI = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def _rank(i: int) -> str:
    return RANK_EMOJI[i] if i < len(RANK_EMOJI) else f"{i + 1}."


# ============================================================
# 早盤選股（morning）
# ============================================================
def morning(date_slash: str, spy: float, qqq: float,
            stocks: list, scanner_count) -> str:
    """
    date_slash : 'YYYY/MM/DD'
    spy, qqq   : float（百分比數值，例 0.02 表 +0.02%）
    stocks     : list[dict] 每筆含 name, code, price, winrate, gain, ml(可None)
    scanner_count : int 或字串（paused / n/a）
    """
    lines = [
        HEADER_MORNING,
        BAR,
        f"📅 今日預測 {date_slash}",
        f"🌍 SPY {spy:+.2f}% | QQQ {qqq:+.2f}%",
        BAR,
    ]
    for i, s in enumerate(stocks):
        lines.append(f"{_rank(i)} {s['name']} {s['code']} 💰{s['price']:.2f}")
        stat = f"📈 勝率 {s['winrate']:.1f}% | 預測 {s['gain']:+.2f}%"
        if MORNING_SHOW_ML and s.get("ml") is not None:
            stat += f" 🤖{s['ml']:.1f}"
        lines.append(stat)
        if MORNING_SHOW_PANEL and s.get("consensus") is not None:
            lines.append(f"🧑‍💼 分析師會議：{s['consensus']} (信心{s.get('confidence', 0):.0%})")
    lines.append(BAR)
    lines.append(f"📌 收盤後自動驗證{LP}掃描全市場 {scanner_count} 檔{RP}")
    return "\n".join(lines)


def morning_empty(date_slash: str, spy: float, qqq: float,
                  reason: str, scanner_count) -> str:
    """fail-safe：掃描/篩選為空、或無標的時的空結果通知（仍推播，不靜默）。"""
    return "\n".join([
        HEADER_MORNING,
        BAR,
        f"📅 今日預測 {date_slash}",
        f"🌍 SPY {spy:+.2f}% | QQQ {qqq:+.2f}%",
        BAR,
        f"😶 {reason}",
        BAR,
        f"📌 收盤後自動驗證{LP}掃描全市場 {scanner_count} 檔{RP}",
    ])


def morning_paused(date_slash: str, spy: float, qqq: float) -> str:
    """美股大跌暫停選股通知。"""
    return "\n".join([
        HEADER_MORNING,
        BAR,
        f"📅 今日預測 {date_slash}",
        f"🌍 SPY {spy:+.2f}% | QQQ {qqq:+.2f}%",
        BAR,
        "⚠️ 美股大跌，今日暫停選股",
        BAR,
    ])


# ============================================================
# 收盤驗證（verify）
# ============================================================
def verify(date_dash: str, results: list) -> str:
    """
    date_dash : 'YYYY-MM-DD'
    results   : list[dict] 每筆含 name, code, winrate,
                actual_pct(signed float), correct(bool)
    """
    hits = sum(1 for r in results if r["correct"])
    total = len(results)
    pct = round(hits / total * 100) if total else 0

    lines = []
    if VERIFY_TOP_BORDER:
        lines.append(BAR)
    if VERIFY_INNER_HEADER:
        lines.append(VERIFY_INNER_HEADER)
    lines.append(f"📊 預測驗證報告 {date_dash}")
    lines.append(f"✅ 今日準確率: {hits}/{total}{LP}{pct}%{RP}")
    lines.append(BAR)

    for i, r in enumerate(results):
        ap = r["actual_pct"]
        arrow = "↑" if ap >= 0 else "↓"
        mark = "✅ 正確" if r["correct"] else "❌ 錯誤"
        lines.append(f"{_rank(i)} {r['name']} {r['code']}")
        lines.append(
            f"預測↑{LP}{r['winrate']:.1f}%{RP} | 實際{arrow} "
            f"{arrow}{abs(ap):.2f}%  {mark}"
        )
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    lines.append(BAR)
    return "\n".join(lines)


def verify_empty(date_dash: str) -> str:
    parts = []
    if VERIFY_TOP_BORDER:
        parts.append(BAR)
    parts += [
        f"📊 預測驗證報告 {date_dash}",
        "📭 今日無到期可驗證之預測",
        BAR,
    ]
    return "\n".join(parts)


# ============================================================
# 週報：本週準確率（非契約指定格式，沿用 verify 風格，可調）
# ============================================================
def weekly_summary(date_dash: str, hits: int, total: int) -> str:
    pct = round(hits / total * 100) if total else 0
    return "\n".join([
        BAR,
        f"📈 本週準確率週報 {date_dash}",
        f"✅ 本週累計: {hits}/{total}{LP}{pct}%{RP}",
        BAR,
    ])


# ============================================================
# 週五 ML 回測報告（契約指定格式）
# ============================================================
def ml_backtest(n_samples: int, base_winrate: float, avg_acc: float,
                avg_auc: float) -> str:
    """USER LAYER：僅呈現乾淨指標，禁止 ML 術語/特徵重要性/CV 細節。"""
    return "\n".join([
        HEADER_ML_BACKTEST,
        BAR,
        f"樣本總數:{n_samples} 筆",
        f"基準勝率{LP}真實{RP}:{base_winrate:.1f}%",
        f"平均準確率:{avg_acc:.1f}%",
        f"平均 AUC:{avg_auc:.1f}%",
        BAR,
    ])


# ============================================================
# 測試訊息（test mode）
# ============================================================
def test_msg(now_str: str) -> str:
    return "\n".join([
        BAR,
        "✅ ai-stock-bot 推播測試",
        "Token 與推播管道正常",
        f"時間 {now_str}",
        BAR,
    ])
