# -*- coding: utf-8 -*-
"""
core/filter.py
技術分析濾網。
輸入個股歷史 DataFrame，計算指標並判斷是否通過：
- MA20：收盤須站上 20 日均線
- RSI(14)：須落在 [RSI_MIN, RSI_MAX]
- 成交量比 vx：當日量 / 近 20 日均量 ≥ VOL_RATIO_MIN
- K 棒收盤位置 hi_lo_pos：當日 (Close-Low)/(High-Low)，偏高較佳

回傳 (passed: bool, features: dict)；資料不足回 (False, {})。
"""

import config
from utils.logger import get_logger

log = get_logger("filter")


def _rsi(closes, period):
    if len(closes) < period + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(-period, 0):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gains += d
        else:
            losses -= d
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_features(df) -> dict:
    """從 DataFrame 計算指標特徵；不足回 {}。"""
    try:
        closes = list(df["Close"].dropna())
        highs = list(df["High"].dropna())
        lows = list(df["Low"].dropna())
        vols = list(df["Volume"].dropna())
        if len(closes) < config.MA_PERIOD + 1:
            return {}

        close = closes[-1]
        ma20 = sum(closes[-config.MA_PERIOD:]) / config.MA_PERIOD
        rsi = _rsi(closes, config.RSI_PERIOD)
        if rsi is None:
            return {}

        avg_vol = sum(vols[-config.MA_PERIOD:]) / config.MA_PERIOD if vols else 0
        vx = (vols[-1] / avg_vol) if avg_vol else 0.0

        prev_close = closes[-2]
        chg = (close / prev_close - 1) * 100 if prev_close else 0.0
        ma20_diff = (close / ma20 - 1) * 100 if ma20 else 0.0

        hi, lo = highs[-1], lows[-1]
        hi_lo_pos = (close - lo) / (hi - lo) if (hi - lo) else 0.5

        # weekday：以最後一筆日期推算（0=Mon）
        try:
            weekday = df.index[-1].weekday()
        except Exception:  # noqa: BLE001
            weekday = 0

        return {
            "close": round(close, 2),
            "ma20": round(ma20, 2),
            "rsi": round(rsi, 2),
            "vx": round(vx, 3),
            "chg": round(chg, 2),
            "ma20_diff": round(ma20_diff, 2),
            "hi_lo_pos": round(hi_lo_pos, 3),
            "weekday": int(weekday),
        }
    except Exception as e:  # noqa: BLE001
        log.warning(f"指標計算失敗：{e}")
        return {}


def passes(feat: dict) -> bool:
    if not feat:
        return False
    if feat["close"] < feat["ma20"]:
        return False
    if not (config.RSI_MIN <= feat["rsi"] <= config.RSI_MAX):
        return False
    if feat["vx"] < config.VOL_RATIO_MIN:
        return False
    return True
