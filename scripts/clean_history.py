# -*- coding: utf-8 -*-
"""
scripts/clean_history.py — history.csv 一次性清理（Gate-A / EDR-001 S4）

⚠️ 一次性工具，不納入 Production 流程（不被 workflow 呼叫）。

流程（Condition A：強制 Dry Run，禁止直接 replace）：
    BACKUP → CANDIDATE → VALIDATOR → DIFF REPORT → [CP2 Supervisor Approval] → REPLACE

清理規則：
    (a) 移除非交易日列（週六 / 週日）
    (b) 移除重複鍵 (date, code)，保留 first occurrence

用法：
    python scripts/clean_history.py              # Dry Run（預設，不 replace）
    python scripts/clean_history.py --replace    # 僅在 CP2 核准後使用
"""

import csv
import datetime
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import data_validator  # noqa: E402

BACKUP_DIR = os.path.join(config.DATA_DIR, "backups")
CANDIDATE_PATH = os.path.join(config.DATA_DIR, "history_candidate.csv")


def _read(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=config.HISTORY_HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in config.HISTORY_HEADER})


def _label_stats(rows):
    l1 = sum(1 for r in rows if str(r.get("target_label", "")).strip() == "1")
    l0 = sum(1 for r in rows if str(r.get("target_label", "")).strip() == "0")
    return l1, l0, len(rows) - l1 - l0


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dst = os.path.join(BACKUP_DIR, f"history_{ts}.csv")
    shutil.copy2(config.HISTORY_PATH, dst)
    same = os.path.getsize(dst) == os.path.getsize(config.HISTORY_PATH)
    print(f"[1] BACKUP    : {dst}  (byte-size match: {same})")
    if not same:
        raise RuntimeError("備份檔大小不符，中止")
    return dst


def build_candidate():
    rows = _read(config.HISTORY_PATH)
    deleted_nontrading, deleted_dup = [], []

    step1 = []
    for i, r in enumerate(rows, start=2):
        try:
            is_wk = datetime.date.fromisoformat((r.get("date") or "").strip()).weekday() >= 5
        except ValueError:
            is_wk = False
        if is_wk:
            deleted_nontrading.append((i, r))
        else:
            step1.append((i, r))

    seen, kept = {}, []
    for i, r in step1:
        key = ((r.get("date") or "").strip(), (r.get("code") or "").strip())
        if key in seen:
            deleted_dup.append((i, r, seen[key]))
            continue
        seen[key] = i
        kept.append(r)

    _write(CANDIDATE_PATH, kept)
    print(f"[2] CANDIDATE : {CANDIDATE_PATH}  ({len(kept)} rows)")
    return rows, kept, deleted_nontrading, deleted_dup


def diff_report(orig, kept, del_nt, del_dup):
    print("[4] DIFF REPORT")
    print("=" * 60)
    print("DIFF REPORT — history.csv cleaning")
    print("=" * 60)

    print(f"\n(1) DELETED ROWS — non-trading day : {len(del_nt)}")
    for i, r in del_nt:
        d = r.get("date", "")
        try:
            wd = datetime.date.fromisoformat(d).strftime("%A")
        except ValueError:
            wd = "?"
        lab = r.get("target_label", "") or "(empty)"
        print(f"    Removed: row {i:>3}  {d}  {r.get('code','')}"
              f"  label={lab}  Reason: non-trading day ({wd})")

    print(f"\n(2) DUPLICATE RESOLUTION : {len(del_dup)}")
    for i, r, first in del_dup:
        lab = r.get("target_label", "") or "(empty)"
        print(f"    Duplicate key: {r.get('date','')} / {r.get('code','')}")
        print(f"      Keep   : row {first}  (first occurrence)")
        print(f"      Remove : row {i}  label={lab}")
        print(f"      Reason : first occurrence policy")

    b1, b0, bb = _label_stats(orig)
    a1, a0, ab = _label_stats(kept)
    print("\n(3) LABEL IMPACT (measured, not assumed)")
    print(f"    {'':<16}{'Before':>8}{'After':>8}{'Delta':>8}")
    print(f"    {'Total rows':<16}{len(orig):>8}{len(kept):>8}{len(kept)-len(orig):>8}")
    print(f"    {'label = 1':<16}{b1:>8}{a1:>8}{a1-b1:>8}")
    print(f"    {'label = 0':<16}{b0:>8}{a0:>8}{a0-b0:>8}")
    print(f"    {'unlabeled':<16}{bb:>8}{ab:>8}{ab-bb:>8}")
    print(f"    {'labeled total':<16}{b1+b0:>8}{a1+a0:>8}{(a1+a0)-(b1+b0):>8}")
    print("=" * 60)
    return (b1 + b0) == (a1 + a0)


def main():
    do_replace = "--replace" in sys.argv

    orig_res = data_validator.validate(config.HISTORY_PATH)
    print(f"[0] PRE-CHECK : current history.csv → "
          f"{'PASS' if orig_res['passed'] else 'FAIL'} "
          f"(dup={len(orig_res['duplicates'])}, "
          f"non-trading={len(orig_res['non_trading_days'])})\n")

    backup()
    orig, kept, del_nt, del_dup = build_candidate()

    cand_res = data_validator.validate(CANDIDATE_PATH)
    print(f"[3] VALIDATOR : candidate → {'PASS' if cand_res['passed'] else 'FAIL'} "
          f"(rows={cand_res['total']}, labeled={cand_res['labeled']}, "
          f"dup={len(cand_res['duplicates'])}, "
          f"non-trading={len(cand_res['non_trading_days'])})\n")

    label_ok = diff_report(orig, kept, del_nt, del_dup)

    dry_pass = cand_res["passed"] and label_ok
    print(f"\n[5] DRY RUN   : {'PASS' if dry_pass else 'FAIL'}")

    if not do_replace:
        print("\n⛔ REPLACE NOT PERFORMED — Dry Run only (Condition A).")
        print("   history.csv 未被修改。")
        print("   須經 CP2 Supervisor 核准後，方可執行：")
        print("     python scripts/clean_history.py --replace")
        return 0 if dry_pass else 1

    if not dry_pass:
        print("\n⛔ DRY RUN FAILED — 中止 replace。")
        return 1

    shutil.move(CANDIDATE_PATH, config.HISTORY_PATH)
    print("\n[6] REPLACE   : history.csv 已更新（candidate → history.csv）")
    final = data_validator.validate(config.HISTORY_PATH)
    print(f"[7] POST-CHECK: {'PASS' if final['passed'] else 'FAIL'} "
          f"(rows={final['total']}, labeled={final['labeled']})")
    return 0 if final["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
