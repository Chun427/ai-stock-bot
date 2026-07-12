# -*- coding: utf-8 -*-
"""
core/verifier.py
收盤驗證：驗證所有 verified=false 且已達 5 個交易日的預測。
5 日波段標記：
- 逐日掃描買入後最多 5 個交易日的 High / Low
- 任一日 Low 跌幅 ≤ -1.5% → 停損，強制標記失敗（即使後來漲回）
- 任一日 High 漲幅 > +3%（且未先停損）→ 命中
- 回填 target_label 至 history.csv，標記 db 該筆 verified=true
回傳 (results, due_count)；results 供 formatter.verify 使用。
"""

from datetime import datetime

import config
from utils.logger import get_logger
from core import market_data
from storage import history

log = get_logger("verifier")


def _label_and_actual(df, buy_price):
    """回傳 (label:int, actual_pct:float, mature:bool)。

    績效與交易規則對齊（Performance Metric Alignment）：
      1) 先觸停利 High ≥ +3%  → actual_pct = +3%（於停利點出場）
      2) 先觸停損 Low  ≤ -1.5% → actual_pct = -1.5%（於停損點出場）
      3) 5 日內皆未觸發        → actual_pct = 第 5 日 close 相對買價
    停損優先於停利（同日先檢查 Low，與原邏輯一致）。
    label 判定規則不變：命中且未先停損 → 1，否則 0。
    """
    highs = list(df["High"].dropna())
    lows = list(df["Low"].dropna())
    closes = list(df["Close"].dropna())
    if len(closes) < 1:
        return None, None, False

    n = min(config.VERIFY_WINDOW, len(highs))
    mature = len(highs) >= config.VERIFY_WINDOW
    hit, stopped = False, False
    for k in range(n):
        lo_chg = lows[k] / buy_price - 1
        hi_chg = highs[k] / buy_price - 1
        if lo_chg <= config.STOP_THRESHOLD:
            stopped = True
            break
        if hi_chg > config.HIT_THRESHOLD:
            hit = True
            break
    label = 1 if (hit and not stopped) else 0

    # 依實際出場方式計算報酬（模擬真實交易）
    if stopped:
        actual_pct = config.STOP_THRESHOLD * 100          # 停損出場
    elif hit:
        actual_pct = config.HIT_THRESHOLD * 100           # 停利出場
    else:
        actual_pct = (closes[min(n, len(closes)) - 1] / buy_price - 1) * 100  # 時間出場
    return label, round(actual_pct, 2), mature


def verify_due(db: dict):
    """處理 db 中所有未驗證且到期的預測。直接就地修改 db。"""
    results = []
    due = 0
    for key, rec in db.items():
        if not key.startswith("PRED_"):
            continue
        if rec.get("verified"):
            continue
        buy_date = rec.get("date")
        stocks = rec.get("stocks", [])
        if not buy_date or not stocks:
            continue

        rec_results = []
        all_mature = True
        for s in stocks:
            code = s.get("code")
            buy = s.get("price")
            ticker = s.get("ticker")
            if buy in (None, 0):
                all_mature = False
                continue
            # 取買入日之後的歷史
            df = (market_data.get_history_by_ticker(ticker, config.VERIFY_WINDOW + 30)
                  if ticker else None)
            if df is None:
                df, _ = market_data.get_history(code, config.VERIFY_WINDOW + 30)
            if df is None:
                all_mature = False
                continue
            try:
                after = df[df.index.strftime("%Y-%m-%d") > buy_date]
            except Exception:  # noqa: BLE001
                after = df
            label, actual_pct, mature = _label_and_actual(after, buy)
            if label is None:
                all_mature = False
                continue
            if not mature:
                all_mature = False
                continue
            history.backfill_label(buy_date, code, label)
            s["label"] = label          # 寫回 db 供週報統計
            s["actual_pct"] = actual_pct
            rec_results.append({
                "name": s.get("name"), "code": code,
                "winrate": s.get("winrate", 0.0),
                "actual_pct": actual_pct, "correct": bool(label),
            })

        if rec_results and all_mature:
            due += 1
            rec["verified"] = True
            results.extend(rec_results)
            log.ok(f"{key} 已驗證 {len(rec_results)} 檔")

    return results, due


def latest_unverified_date(db: dict):
    dates = [rec.get("date") for k, rec in db.items()
             if k.startswith("PRED_") and not rec.get("verified")]
    return max(dates) if dates else datetime.now().strftime("%Y-%m-%d")
