# -*- coding: utf-8 -*-
"""
ml/backtest_engine.py — 真實市場 Walk-forward 回測引擎
========================================================
無未來資料洩漏：第 t 期選股只用 df.loc[:t]，評估看 t→t+HOLD。
非重疊再平衡（每 HOLD 交易日一期），可正確算 Sharpe / 年化 / MDD。
扣台股交易成本。基準：Random / Index Buy&Hold / 全 universe 等權。
輸出：每筆交易 CSV + Markdown 報告。

執行（任何有網路環境）：
    python main.py --mode backtest
無網路時 run() 可吃合成 panel 做管線自測（非真實績效）。
"""
import csv
import os
import random
from datetime import datetime

import numpy as np
import pandas as pd

import config
from core import scorer
from ml import costs
from utils.logger import get_logger

log = get_logger("backtest_engine")

HOLD = config.BT_HOLD_DAYS
TOP_N = config.BT_TOP_N
PERIODS_PER_YEAR = 252.0 / HOLD


def load_panel(codes: list, years: int = None):
    """用 market_data 抓真實歷史，組成 {code: DataFrame[Close,High,Low]}。"""
    from core import market_data
    years = years or config.BT_YEARS
    panel, index_series = {}, None
    for code in codes:
        try:
            df, _ = market_data.get_history(code)
            if df is None or len(df) < config.MA_PERIOD + HOLD + 5:
                continue
            panel[code] = df[["Close", "High", "Low"]].dropna()
        except Exception as e:  # noqa: BLE001
            log.warning(f"{code} 歷史抓取失敗：{e}")
    try:
        from core import market_data as md
        idf = md.get_history_by_ticker(config.BT_INDEX_TICKER, days=years * 365)
        if idf is not None and "Close" in idf:
            index_series = idf["Close"].dropna()
    except Exception as e:  # noqa: BLE001
        log.warning(f"指數基準抓取失敗：{e}")
    log.info(f"panel 組成 {len(panel)} 檔（要求 {len(codes)} 檔）")
    return panel, index_series


def _equity_metrics(rets: list) -> dict:
    if not rets:
        return {"n": 0}
    r = np.array(rets, dtype=float)
    eq = np.cumprod(1 + r)
    peak = np.maximum.accumulate(eq)
    mdd = float(((eq - peak) / peak).min())
    total = float(eq[-1] - 1)
    ann = float((eq[-1]) ** (PERIODS_PER_YEAR / len(r)) - 1) if eq[-1] > 0 else -1.0
    sharpe = float(np.mean(r) / np.std(r) * np.sqrt(PERIODS_PER_YEAR)) if np.std(r) > 0 else 0.0
    return {
        "n": len(r),
        "total_return": round(total * 100, 2),
        "annualized": round(ann * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(mdd * 100, 2),
        "win_rate": round(float(np.mean(r > 0)) * 100, 1),
        "avg_period_ret": round(float(np.mean(r)) * 100, 2),
    }


def run(panel: dict, index_series: pd.Series = None, seed: int = None):
    """回測主程式。回傳 (summary_dict, trades_list)。"""
    seed = config.BT_RANDOM_SEED if seed is None else seed
    random.seed(seed)
    tickers = list(panel.keys())
    if len(tickers) < TOP_N:
        return {"error": f"universe 僅 {len(tickers)} 檔，不足 TOP_N={TOP_N}"}, []

    dates = panel[tickers[0]].index
    min_hist = config.MA_PERIOD + HOLD + 5

    model_rets, random_rets, market_rets, index_rets = [], [], [], []
    model_hits = []
    trades = []

    t = min_hist
    while t < len(dates) - HOLD:
        rebal_date = dates[t]
        elig = []
        for tk in tickers:
            df = panel[tk]
            if t >= len(df):
                continue
            hist = df.iloc[: t + 1]                    # ★ 只到 t，無洩漏
            if len(hist) < min_hist:
                continue
            sc = scorer.score(hist, 0.0)
            if sc:
                elig.append((tk, sc["score"]))
        if len(elig) < TOP_N:
            t += HOLD
            continue

        elig.sort(key=lambda x: -x[1])
        picks = [tk for tk, _ in elig[:TOP_N]]
        rand_picks = random.sample([tk for tk, _ in elig], TOP_N)

        def _net(tk):
            df = panel[tk]
            buy = float(df["Close"].values[t])
            sell = float(df["Close"].values[min(t + HOLD, len(df) - 1)])
            return buy, sell, costs.round_trip_net(buy, sell)

        # 模型 Top-N（等權）
        prets = []
        for tk in picks:
            buy, sell, net = _net(tk)
            prets.append(net)
            # precision@5：用線上同一命中規則（intrabar +3% 先於 -1.5%）
            df = panel[tk]
            hi = df["High"].values; lo = df["Low"].values; cl = df["Close"].values
            b = cl[t]; hit = False; stop = False
            for k in range(1, min(HOLD, len(cl) - 1 - t) + 1):
                if lo[t + k] / b - 1 <= config.STOP_THRESHOLD:
                    stop = True; break
                if hi[t + k] / b - 1 > config.HIT_THRESHOLD:
                    hit = True; break
            model_hits.append(1 if (hit and not stop) else 0)
            trades.append({
                "rebal_date": rebal_date.strftime("%Y-%m-%d"),
                "code": tk, "buy": round(buy, 2), "sell": round(sell, 2),
                "net_return_pct": round(net * 100, 2),
                "hit": 1 if (hit and not stop) else 0,
            })
        model_rets.append(float(np.mean(prets)))

        rrets = [_net(tk)[2] for tk in rand_picks]
        random_rets.append(float(np.mean(rrets)))

        # 市場基準：全 universe 等權（扣成本）
        mrets = [_net(tk)[2] for tk in tickers if t < len(panel[tk])]
        if mrets:
            market_rets.append(float(np.mean(mrets)))

        # 指數買進持有（同期，扣一次來回成本）
        if index_series is not None and t + HOLD < len(index_series):
            ib = float(index_series.values[t]); isell = float(index_series.values[t + HOLD])
            index_rets.append(costs.round_trip_net(ib, isell))

        # 附記每筆交易的當期指數報酬，便於 CSV 對照
        if trades and index_rets:
            for tr in trades[-len(picks):]:
                tr["index_ret_pct"] = round(index_rets[-1] * 100, 2)

        t += HOLD                                       # 非重疊

    summary = {
        "params": {
            "hold_days": HOLD, "top_n": TOP_N,
            "fee": config.FEE_RATE, "tax": config.TAX_RATE, "slippage": config.SLIPPAGE,
            "cost_drag_per_trade_pct": round(costs.cost_drag() * 100, 3),
            "universe_size": len(tickers), "periods": len(model_rets),
        },
        "model": _equity_metrics(model_rets),
        "random": _equity_metrics(random_rets),
        "market_ew": _equity_metrics(market_rets),
        "index_buyhold": _equity_metrics(index_rets),
        "precision_at_n": round(float(np.mean(model_hits)) * 100, 1) if model_hits else 0.0,
    }
    # 超額報酬（年化，對指數）
    if summary["model"].get("annualized") is not None and summary["index_buyhold"].get("annualized") is not None:
        summary["excess_vs_index_ann_pct"] = round(
            summary["model"]["annualized"] - summary["index_buyhold"]["annualized"], 2)
    return summary, trades


def write_outputs(summary: dict, trades: list, tag: str = None) -> tuple:
    os.makedirs(config.BT_OUTPUT_DIR, exist_ok=True)
    tag = tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(config.BT_OUTPUT_DIR, f"trades_{tag}.csv")
    md_path = os.path.join(config.BT_OUTPUT_DIR, f"report_{tag}.md")

    cols = ["rebal_date", "code", "buy", "sell", "net_return_pct", "hit", "index_ret_pct"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for tr in trades:
            w.writerow({c: tr.get(c, "") for c in cols})

    m, rnd, mk, ix = (summary.get(k, {}) for k in ("model", "random", "market_ew", "index_buyhold"))
    lines = [
        "# ai-stock-bot 回測報告（含交易成本）",
        f"產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- 持有天數：{summary['params']['hold_days']} 交易日 / 每期選股：{summary['params']['top_n']}",
        f"- universe：{summary['params']['universe_size']} 檔 / 期數：{summary['params']['periods']}",
        f"- 成本：手續費 {config.FEE_RATE*100:.4f}% × 2 + 證交稅 {config.TAX_RATE*100:.2f}% + 滑價 {config.SLIPPAGE*100:.2f}% × 2"
        f"（每筆來回拖累約 {summary['params']['cost_drag_per_trade_pct']}%）",
        "",
        "## 績效比較（皆為扣成本後淨值）",
        "",
        "| 指標 | 模型 Top5 | 隨機 | 全市場等權 | 指數買持(0050) |",
        "|---|---|---|---|---|",
        f"| 總報酬 % | {m.get('total_return')} | {rnd.get('total_return')} | {mk.get('total_return')} | {ix.get('total_return')} |",
        f"| 年化 % | {m.get('annualized')} | {rnd.get('annualized')} | {mk.get('annualized')} | {ix.get('annualized')} |",
        f"| Sharpe | {m.get('sharpe')} | {rnd.get('sharpe')} | {mk.get('sharpe')} | {ix.get('sharpe')} |",
        f"| 最大回撤 % | {m.get('max_drawdown')} | {rnd.get('max_drawdown')} | {mk.get('max_drawdown')} | {ix.get('max_drawdown')} |",
        f"| 勝率 % | {m.get('win_rate')} | {rnd.get('win_rate')} | {mk.get('win_rate')} | {ix.get('win_rate')} |",
        f"| 平均每期 % | {m.get('avg_period_ret')} | {rnd.get('avg_period_ret')} | {mk.get('avg_period_ret')} | {ix.get('avg_period_ret')} |",
        "",
        f"- Precision@{TOP_N}（命中 +3% 規則）：{summary.get('precision_at_n')}%",
        f"- 對指數年化超額報酬：{summary.get('excess_vs_index_ann_pct')}%",
        "",
        "## 結論判讀",
        "若『模型年化』未持續且明顯高於『指數買持』與『隨機』，則本策略**無投資優勢**，",
        "依監督結論應停止優化。Accuracy 高但績效不優於基準，對目標無價值。",
    ]
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return csv_path, md_path
