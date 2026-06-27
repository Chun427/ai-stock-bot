# -*- coding: utf-8 -*-
"""
core/market_data.py
統一行情資料存取層（yfinance）。
- 每次下載 retry × 3，含逾時保護（修正先前「缺 per-call timeout」風險）
- TW 代號自動嘗試 .TW（上市）/ .TWO（上櫃）
- 任一檔失敗回傳 None，呼叫端跳過，不中斷整體
"""

import time

import config
from utils.logger import get_logger

log = get_logger("market_data")

try:
    import yfinance as yf
    _YF = True
except Exception as e:  # noqa: BLE001
    log.error(f"yfinance 匯入失敗：{e}")
    _YF = False


def _download(ticker: str, days: int):
    """回傳含 Open/High/Low/Close/Volume 的 DataFrame，失敗回 None。"""
    if not _YF:
        return None
    period = f"{max(days + 10, 30)}d"
    for attempt in range(1, 4):
        try:
            df = yf.Ticker(ticker).history(period=period, timeout=config.NET_TIMEOUT)
            if df is not None and not df.empty:
                return df.tail(days)
        except Exception as e:  # noqa: BLE001
            log.warning(f"{ticker} 下載失敗 attempt {attempt}: {e}")
        time.sleep(attempt)
    return None


def get_history(code: str, days: int = None):
    """以股票代號取得歷史（自動嘗試 .TW / .TWO）。回傳 (df, resolved_ticker) 或 (None, None)。"""
    days = days or config.HISTORY_DAYS
    for suffix in (".TW", ".TWO"):
        df = _download(f"{code}{suffix}", days)
        if df is not None and len(df) >= 20:
            return df, f"{code}{suffix}"
    log.warning(f"{code} 無可用歷史資料")
    return None, None


def get_history_by_ticker(ticker: str, days: int):
    """已知完整 ticker（含後綴或美股代號）時直接抓。"""
    return _download(ticker, days)


def get_us_market():
    """
    回傳 (spy_pct, qqq_pct, crashed)
    spy 以 ^GSPC 最近兩日收盤計算；推播顯示標籤為 SPY。
    任一抓取失敗以 0.0 計，crashed=False（fail-safe：不因抓不到而誤暫停）。
    """
    def pct(ticker):
        df = _download(ticker, 5)
        if df is None or len(df) < 2:
            return None
        c = df["Close"].dropna()
        if len(c) < 2 or c.iloc[-2] == 0:
            return None
        return (c.iloc[-1] / c.iloc[-2] - 1) * 100.0

    spy = pct(config.US_INDEX)
    qqq = pct(config.US_QQQ)
    spy_v = spy if spy is not None else 0.0
    qqq_v = qqq if qqq is not None else 0.0

    crashed = False
    if spy is not None and qqq is not None:
        thr = config.US_CRASH_THRESHOLD * 100.0  # -0.5
        crashed = (spy_v <= thr) and (qqq_v <= thr)
    return spy_v, qqq_v, crashed
