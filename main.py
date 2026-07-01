# -*- coding: utf-8 -*-
"""
main.py
程式入口：MODE 分派 + [REPORT] 強制輸出 + 頂層例外攔截。
即使 pipeline 中途例外，[REPORT] 仍會輸出，GitHub Actions 不靜默中斷。
"""

from datetime import datetime

import config
from utils.logger import get_logger
from push import formatter, telegram, line
from storage import db as dbstore, history, git_sync

log = get_logger("main")

REPORT = {
    "mode": config.MODE,
    "scanner": "n/a",
    "filter": "n/a",
    "final": "n/a",
    "push_telegram": "not_run",
    "push_line": "not_run",
    "db_update": "n/a",
}


def push_all(text: str):
    tg = telegram.push(text)
    ln = line.push(text)
    REPORT["push_telegram"] = tg
    REPORT["push_line"] = ln
    return tg, ln


# ============================================================
# MODE: test
# ============================================================
def run_test():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    push_all(formatter.test_msg(now))


# ============================================================
# MODE: morning
# ============================================================
def run_morning():
    from core import market_data, scanner, filter as tfilter, scorer
    from ml import ml_model

    today_slash = datetime.now().strftime("%Y/%m/%d")
    today_dash = datetime.now().strftime("%Y-%m-%d")

    spy, qqq, crashed = market_data.get_us_market()
    if crashed:
        log.warning("美股大跌，今日暫停選股")
        REPORT["scanner"] = "paused"
        push_all(formatter.morning_paused(today_slash, spy, qqq))
        return

    candidates = scanner.scan()
    REPORT["scanner"] = len(candidates)
    if not candidates:
        push_all(formatter.morning_empty(today_slash, spy, qqq,
                                         "掃描來源無資料", 0))
        return

    adj = scorer.us_adjust(spy, qqq)
    passed = []
    for c in candidates:
        df, ticker = market_data.get_history(c["code"])
        if df is None:
            continue
        feat = tfilter.compute_features(df)
        if not tfilter.passes(feat):
            continue
        sc = scorer.score(df, adj)
        if sc is None:
            continue
        passed.append({**c, "ticker": ticker, "feat": feat, "sc": sc})

    REPORT["filter"] = len(passed)
    if not passed:
        push_all(formatter.morning_empty(today_slash, spy, qqq,
                                         "今日無符合條件之標的", len(candidates)))
        return

    passed.sort(key=lambda x: -x["sc"]["score"])
    top = passed[: config.TOP_N]
    REPORT["final"] = len(top)

    push_stocks, db_stocks, hist_rows = [], [], []
    for t in top:
        feat, sc = t["feat"], t["sc"]
        ml = ml_model.predict_score(feat)
        push_stocks.append({
            "name": t["name"], "code": t["code"], "price": feat["close"],
            "winrate": sc["winrate"], "gain": sc["pred_gain"], "ml": ml,
        })
        db_stocks.append({
            "name": t["name"], "code": t["code"], "price": feat["close"],
            "ticker": t["ticker"], "winrate": sc["winrate"], "label": None,
        })
        hist_rows.append({
            "date": today_dash, "code": t["code"], "name": t["name"],
            "rsi": feat["rsi"], "vx": feat["vx"], "chg": feat["chg"],
            "ma20_diff": feat["ma20_diff"], "hi_lo_pos": feat["hi_lo_pos"],
            "weekday": feat["weekday"], "target_label": "",
        })

    push_all(formatter.morning(today_slash, spy, qqq, push_stocks, len(candidates)))

    history.append_features(hist_rows)
    data = dbstore.load()
    data[dbstore.key_for(today_dash)] = {
        "date": today_dash, "spy": spy, "qqq": qqq,
        "scanner": len(candidates), "stocks": db_stocks, "verified": False,
    }
    REPORT["db_update"] = "success" if dbstore.save(data) else "fail"
    REPORT["db_update"] = _sync_state(f"morning {today_dash}", REPORT["db_update"])


# ============================================================
# MODE: verify
# ============================================================
def run_verify(also_weekly=False):
    from core import verifier
    data = dbstore.load()
    results, due = verifier.verify_due(data)
    date_dash = verifier.latest_unverified_date(data) if not results \
        else datetime.now().strftime("%Y-%m-%d")

    if results:
        push_all(formatter.verify(date_dash, results))
    else:
        push_all(formatter.verify_empty(date_dash))

    REPORT["db_update"] = "success" if dbstore.save(data) else "fail"
    REPORT["db_update"] = _sync_state(f"verify {date_dash}", REPORT["db_update"])
    return data


# ============================================================
# MODE: weekly
# ============================================================
def run_weekly():
    from core import weekly_report
    from ml import trainer, backtest

    # 先執行當日驗證（含推播 + 寫回）
    data = run_verify()

    # 本週準確率週報
    hits, total = weekly_report.summarize(data)
    push_all(formatter.weekly_summary(datetime.now().strftime("%Y-%m-%d"),
                                      hits, total))

    # 重訓 + 回測
    trainer.train()
    metrics = backtest.run()
    if metrics:
        # USER LAYER：僅推乾淨指標；特徵重要性/CV 已於 backtest 記入 MODEL log
        push_all(formatter.ml_backtest(
            metrics["n_samples"], metrics["base_winrate"],
            metrics["avg_acc"], metrics["avg_auc"],
        ))
    else:
        log.info("樣本不足，本週不推播 ML 回測報告")

    st = _sync_state("weekly retrain", "success")
    REPORT["db_update"] = st


# ============================================================
# MODE: backtest（投資有效性驗證；離線分析，不推播）
# ============================================================
def run_backtest():
    from core import universe
    from ml import backtest_engine
    REPORT["mode"] = "backtest"
    codes = universe.backtest_universe()
    panel, index_series = backtest_engine.load_panel(codes)
    REPORT["scanner"] = len(panel)
    summary, trades = backtest_engine.run(panel, index_series)
    if "error" in summary:
        log.error(summary["error"])
        REPORT["final"] = 0
        return
    csv_path, md_path = backtest_engine.write_outputs(summary, trades)
    REPORT["final"] = summary["params"]["periods"]
    log.info(f"模型年化 {summary['model'].get('annualized')}% | "
             f"指數 {summary['index_buyhold'].get('annualized')}% | "
             f"隨機 {summary['random'].get('annualized')}% | "
             f"超額 {summary.get('excess_vs_index_ann_pct')}% | "
             f"Precision@{config.TOP_N} {summary.get('precision_at_n')}%")
    log.info(f"CSV：{csv_path}")
    log.info(f"報告：{md_path}")


# ============================================================
# 狀態回寫
# ============================================================
def _sync_state(msg: str, prior: str) -> str:
    res = git_sync.commit_state(msg)
    if res == "fail" or prior == "fail":
        return "fail"
    if res == "success":
        return "success"
    return prior  # n/a → 保留 db.save 結果


# ============================================================
# 入口
# ============================================================
def main():
    log.info("台股 AI 選股系統（ML 升級版）啟動")
    log.info(f"執行模式: {config.MODE}")
    if config.MODE_FALLBACK_USED:
        log.warning("MODE 非白名單值，已 fallback 為 morning")

    try:
        if config.MODE == "test":
            run_test()
        elif config.MODE == "morning":
            run_morning()
        elif config.MODE == "verify":
            run_verify()
        elif config.MODE == "weekly":
            run_weekly()
        elif config.MODE == "backtest":
            run_backtest()
    except Exception as e:  # noqa: BLE001
        import traceback
        log.error(f"頂層例外：{e}")
        traceback.print_exc()
    finally:
        _print_report()


def _print_report():
    log.info("[REPORT]")
    for k in ("mode", "scanner", "filter", "final",
              "push_telegram", "push_line", "db_update"):
        log.info(f"{k+':':<15} {REPORT[k]}")


if __name__ == "__main__":
    import sys
    # CLI 覆蓋：python main.py --mode backtest（MODE 合法性由 scheduler 單一來源裁定）
    if "--mode" in sys.argv:
        import scheduler
        _i = sys.argv.index("--mode")
        if _i + 1 < len(sys.argv):
            _m = sys.argv[_i + 1].strip()
            config.MODE = _m if scheduler.is_valid_mode(_m) else config.MODE
            config.MODE_FALLBACK_USED = not scheduler.is_valid_mode(_m)
            REPORT["mode"] = config.MODE
    main()
