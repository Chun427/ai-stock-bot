# -*- coding: utf-8 -*-
"""
scheduler.py — MODE 解析唯一來源（SINGLE SOURCE OF TRUTH）
==========================================================
Production 觸發為 repository_dispatch（外部排程器準時觸發）。
GitHub cron 已停用（僅保留對應表供 rollback）。

MODE 解析優先序（resolve）：
  1) workflow_dispatch 手動輸入：morning/verify/weekly/test/backtest
  2) repository_dispatch 事件：morning_run/verify_run/weekly_run（去尾 _run）
  3) [rollback] schedule cron → MODE（僅在 workflow 重新啟用 schedule 時作用）

workflow 只呼叫 resolve()，不在 bash/yaml 內判斷 MODE。
"""

# 規範時間對照（台灣 UTC+8）與 rollback 用 cron 對應。
# 正式入口為 repository_dispatch；下方 cron 僅在 workflow schedule 重新啟用時使用。
SCHEDULE = {
    "morning": {"tw": "09:00", "cron_utc": "0 1 * * 1-5",  "desc": "早盤選股（開盤前）"},
    "verify":  {"tw": "14:45", "cron_utc": "45 6 * * 1-4", "desc": "收盤驗證（收盤後）"},
    "weekly":  {"tw": "20:00", "cron_utc": "0 12 * * 5",   "desc": "週回測（週五盤後）"},
}

FALLBACK_MODE = "morning"
VALID_MODES = set(SCHEDULE.keys()) | {"test", "backtest"}


def resolve(schedule_expr: str = "", dispatch_input: str = "",
            dispatch_action: str = "") -> str:
    """唯一 MODE 解析點。優先序：手動輸入 > repository_dispatch > (rollback)schedule。"""
    di = (dispatch_input or "").strip()
    if di:
        return di if is_valid_mode(di) else FALLBACK_MODE
    da = (dispatch_action or "").strip()
    if da:
        mode = da[:-4] if da.endswith("_run") else da   # morning_run → morning
        return mode if is_valid_mode(mode) else FALLBACK_MODE
    return resolve_mode(schedule_expr)


def resolve_mode(schedule_expr: str) -> str:
    """[rollback] 由 cron 字串解析 MODE；無對應則回退 morning。"""
    expr = (schedule_expr or "").strip()
    for mode, meta in SCHEDULE.items():
        if meta["cron_utc"] == expr:
            return mode
    return FALLBACK_MODE


def is_valid_mode(mode: str) -> bool:
    return (mode or "").strip() in VALID_MODES


if __name__ == "__main__":
    # workflow 唯一呼叫點：
    #   python scheduler.py "<schedule>" "<inputs.mode>" "<repository_dispatch action>"
    import sys
    sched = sys.argv[1] if len(sys.argv) > 1 else ""
    disp = sys.argv[2] if len(sys.argv) > 2 else ""
    action = sys.argv[3] if len(sys.argv) > 3 else ""
    print(resolve(sched, disp, action))
