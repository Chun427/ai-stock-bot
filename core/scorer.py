# -*- coding: utf-8 -*-
"""
core/scorer.py
歷史回測評分。
針對單檔個股的 62 日歷史，找出「過去出現相似多頭訊號」的日子，
統計這些訊號日在未來 VERIFY_WINDOW 日內是否達 +3%（且未先觸 -1.5% 停損），
得到：
- winrate：真實勝率（命中數 / 訊號數）
- pred_gain：預測漲幅（訊號日未來最大漲幅平均）
- n_signals：樣本數 → 套用 sample_weight，避免新股假勝率

最終 score = winrate * weight + 美股加減分。
回傳 dict 或 None（樣本不足 / 權重 0）。
"""

import config
from utils.logger import get_logger

log = get_logger("scorer")


def _signal_day(closes, ma_window, i):
    """第 i 日是否為多頭訊號：站上 MA20。"""
    if i < ma_window:
        return False
    ma = sum(closes[i - ma_window:i]) / ma_window
    return closes[i] > ma


def score(df, us_adjust: float):
    try:
        closes = list(df["Close"].dropna())
        highs = list(df["High"].dropna())
        lows = list(df["Low"].dropna())
        n = len(closes)
        if n < config.MA_PERIOD + config.VERIFY_WINDOW + 5:
            return None

        wins, signals, gains = 0, 0, []
        last = n - config.VERIFY_WINDOW  # 留出未來視窗
        for i in range(config.MA_PERIOD, last):
            if not _signal_day(closes, config.MA_PERIOD, i):
                continue
            signals += 1
            buy = closes[i]
            hit, stopped, max_gain = False, False, 0.0
            for k in range(1, config.VERIFY_WINDOW + 1):
                lo_chg = (lows[i + k] / buy - 1)
                hi_chg = (highs[i + k] / buy - 1)
                max_gain = max(max_gain, hi_chg)
                if lo_chg <= config.STOP_THRESHOLD:
                    stopped = True
                    break
                if hi_chg > config.HIT_THRESHOLD:
                    hit = True
                    break
            if hit and not stopped:
                wins += 1
            gains.append(max(max_gain, 0.0))

        if signals == 0:
            return None
        weight = config.sample_weight(signals)
        if weight == 0:
            return None

        winrate = wins / signals * 100.0
        pred_gain = (sum(gains) / len(gains) * 100.0) if gains else 0.0
        base = winrate * weight
        final = base + us_adjust

        return {
            "winrate": round(winrate, 1),
            "pred_gain": round(pred_gain, 2),
            "n_signals": signals,
            "weight": weight,
            "score": round(final, 2),
        }
    except Exception as e:  # noqa: BLE001
        log.warning(f"回測評分失敗：{e}")
        return None


def us_adjust(spy_pct: float, qqq_pct: float) -> float:
    """美股加減分：強勢 +、弱勢 -（範圍約 ±5）。"""
    avg = (spy_pct + qqq_pct) / 2.0
    return max(-5.0, min(5.0, avg * 2.0))
