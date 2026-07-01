# -*- coding: utf-8 -*-
"""
scheduler.py — 單一時間控制中心（SINGLE SOURCE OF TRUTH）
==========================================================
所有任務的規範時間與「schedule → MODE」對應，只在這裡定義。
其他 module 與 workflow 一律引用此處，禁止各自寫死時間。

⚠️ 重要事實（不得宣稱誇大）：
   GitHub Actions 的實際觸發由 GitHub 的 cron 排程器負責，
   高負載時段官方明載「可能延遲數分鐘」。本模組無法消除該延遲，
   它的職責是「定義唯一規範時間 + 解析 MODE」，不是即時觸發器。
   若需『分秒不差』，唯一解是外部排程器/自架 cron，超出本專案範圍。
"""

# 規範時間：台灣（UTC+8）→ GitHub Actions 用的 UTC cron
SCHEDULE = {
    "morning": {"tw": "09:00", "cron_utc": "0 1 * * 1-5",  "desc": "早盤選股（開盤前）"},
    "verify":  {"tw": "14:45", "cron_utc": "45 6 * * 1-4", "desc": "收盤驗證（收盤後）"},
    "weekly":  {"tw": "20:00", "cron_utc": "0 12 * * 5",   "desc": "週回測（週五盤後）"},
}

FALLBACK_MODE = "morning"
VALID_MODES = set(SCHEDULE.keys()) | {"test", "backtest"}


def resolve(schedule_expr: str = "", dispatch_input: str = "",
            dispatch_action: str = "") -> str:
    """唯一 MODE 解析點。優先序：
       1) workflow_dispatch 手動輸入（morning/verify/weekly/test/backtest）
       2) repository_dispatch 事件（morning_run/verify_run/weekly_run → 去尾 _run）
       3) schedule cron → MODE
    workflow 只呼叫此函式，不在 bash/yaml 內判斷 MODE。
    """
    di = (dispatch_input or "").strip()
    if di:
        return di if is_valid_mode(di) else FALLBACK_MODE
    da = (dispatch_action or "").strip()
    if da:
        mode = da[:-4] if da.endswith("_run") else da   # morning_run → morning
        return mode if is_valid_mode(mode) else FALLBACK_MODE
    return resolve_mode(schedule_expr)


def resolve_mode(schedule_expr: str) -> str:
    """由 GitHub 傳入的 cron 字串解析 MODE；無對應則回退 morning。"""
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
