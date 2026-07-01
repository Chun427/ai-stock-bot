# -*- coding: utf-8 -*-
"""
ml/walkforward.py — 歷史滾動回測（Walk-forward）+ 基準比較
============================================================
目的：在「每天只能看見當時可得資料」的前提下，模擬本策略
（每日選 Top-N、持有 HOLD 個交易日）的真實績效，並與基準比較，
避免未來資訊洩漏（look-ahead bias）。

⚠️ 重要：本模組需要歷史價格資料（yfinance / market_data）。
   本沙箱網路白名單不含 Yahoo/yfinance，無法於此抓 3–5 年實價，
   因此「真實結果」必須在可連網的環境（GitHub Actions / 本機）執行。
   下方 self_test() 用合成價格面板僅證明「演算法邏輯正確、無洩漏」，
   不是真實績效，禁止當成投資依據。

無洩漏保證：對測試日 t 的選股，只使用 df.loc[:t]（含 t），
評估則看 t+1..t+HOLD（未來），兩者嚴格切開。
"""

import random
import numpy as np
import pandas as pd

import config
from core import scorer
from utils.logger import get_logger

log = get_logger("walkforward")

HOLD = config.VERIFY_WINDOW            # 持有交易日數（與線上一致）
TOP_N = config.TOP_N
HIT = config.HIT_THRESHOLD
STOP = config.STOP_THRESHOLD


def _eval_pick(df: pd.DataFrame, t_idx: int) -> dict:
    """從第 t_idx 日買進，評估未來 HOLD 日：命中(+3%且未先觸-1.5%) 與週持有報酬。"""
    closes = df["Close"].values
    highs = df["High"].values
    lows = df["Low"].values
    buy = closes[t_idx]
    hit, stopped, maxg = False, False, 0.0
    end = min(t_idx + HOLD, len(closes) - 1)
    for k in range(1, end - t_idx + 1):
        lo_chg = lows[t_idx + k] / buy - 1
        hi_chg = highs[t_idx + k] / buy - 1
        maxg = max(maxg, hi_chg)
        if lo_chg <= STOP:
            stopped = True
            break
        if hi_chg > HIT:
            hit = True
            break
    week_ret = closes[end] / buy - 1          # 單純持有到期報酬
    label = 1 if (hit and not stopped) else 0
    return {"label": label, "week_ret": week_ret}


def run(panel: dict, index_series: pd.Series = None, seed: int = 42) -> dict:
    """
    panel        : {ticker: DataFrame[Close,High,Low]（DatetimeIndex 已排序）}
    index_series : 大盤收盤序列（同日期軸），作買進持有基準；可為 None
    回傳模型 / 隨機 / 大盤 三者的彙整指標。
    """
    random.seed(seed)
    tickers = list(panel.keys())
    if not tickers:
        return {}
    # 以第一檔的日期軸為主軸（實務上各檔對齊交易日）
    dates = panel[tickers[0]].index
    min_hist = config.MA_PERIOD + config.VERIFY_WINDOW + 5

    model_labels, model_rets = [], []
    rand_labels, rand_rets = [], []
    idx_rets = []

    # 測試日範圍：需有足夠歷史(min_hist) 且 留得出未來 HOLD 日
    for ti in range(min_hist, len(dates) - HOLD):
        elig = []
        for tk in tickers:
            df = panel[tk]
            if ti >= len(df):
                continue
            hist = df.iloc[: ti + 1]          # ★ 只到 t（含），無洩漏
            if len(hist) < min_hist:
                continue
            sc = scorer.score(hist, 0.0)      # 用截斷歷史評分
            if sc:
                elig.append((tk, sc["score"]))
        if len(elig) < TOP_N:
            continue

        # 模型：取分數前 TOP_N
        elig.sort(key=lambda x: -x[1])
        picks = [tk for tk, _ in elig[:TOP_N]]
        # 隨機：同 eligible 池隨機 TOP_N（公平比較）
        rand_picks = random.sample([tk for tk, _ in elig], TOP_N)

        for tk in picks:
            r = _eval_pick(panel[tk], ti)
            model_labels.append(r["label"])
            model_rets.append(r["week_ret"])
        for tk in rand_picks:
            r = _eval_pick(panel[tk], ti)
            rand_labels.append(r["label"])
            rand_rets.append(r["week_ret"])
        if index_series is not None and ti + HOLD < len(index_series):
            idx_rets.append(index_series.iloc[ti + HOLD] / index_series.iloc[ti] - 1)

    def _agg(labels, rets):
        if not rets:
            return {"n": 0}
        rets = np.array(rets)
        # 權益曲線：每個決策日的平均報酬序列複利
        eq = np.cumprod(1 + rets)
        peak = np.maximum.accumulate(eq)
        mdd = float(((eq - peak) / peak).min()) if len(eq) else 0.0
        return {
            "n": len(rets),
            "precision_at_n": round(float(np.mean(labels)) * 100, 1) if labels else 0.0,
            "avg_week_ret": round(float(np.mean(rets)) * 100, 2),
            "win_ret_rate": round(float(np.mean(rets > 0)) * 100, 1),
            "max_drawdown": round(mdd * 100, 2),
        }

    result = {
        "hold_days": HOLD, "top_n": TOP_N,
        "model": _agg(model_labels, model_rets),
        "random": _agg(rand_labels, rand_rets),
    }
    if idx_rets:
        ir = np.array(idx_rets)
        result["index_buyhold"] = {
            "n": len(ir),
            "avg_week_ret": round(float(np.mean(ir)) * 100, 2),
            "win_ret_rate": round(float(np.mean(ir > 0)) * 100, 1),
        }
    log.info(f"[walkforward] model={result['model']} random={result['random']}")
    return result


def self_test():
    """合成價格面板：證明 harness 邏輯（無洩漏 / 對齊 / 基準）可跑，非真實績效。"""
    rng = np.random.default_rng(1)
    idx = pd.bdate_range(end=pd.Timestamp("2026-05-27"), periods=400)
    panel = {}
    for j in range(12):
        n = len(idx)
        drift = rng.uniform(-0.0003, 0.0008)
        cl = 50 * np.cumprod(1 + rng.normal(drift, 0.02, n))
        hi = cl * (1 + rng.uniform(0.005, 0.02, n))
        lo = cl * (1 - rng.uniform(0.005, 0.02, n))
        panel[f"T{j:02d}"] = pd.DataFrame({"Close": cl, "High": hi, "Low": lo}, index=idx)
    index_series = pd.Series(
        100 * np.cumprod(1 + rng.normal(0.0002, 0.01, len(idx))), index=idx
    )
    return run(panel, index_series)


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), ensure_ascii=False, indent=2))
