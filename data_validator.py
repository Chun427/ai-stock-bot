# -*- coding: utf-8 -*-
"""
data_validator.py — 資料品質檢查（Gate-A / EDR-001 S3）

READ-ONLY：本模組只讀取與回報，**不修改任何資料**。

檢查項目：
  1. Duplicate Check        (date, code) 不得重複
  2. Trading Day Check      date 不得為週六/週日
  3. Missing Value Check    必要欄位不得為空
  4. Price / Volume Check   數值欄位可解析、非負；rsi ∈ [0,100]；vx > 0

用法：
  python data_validator.py                 # 檢查 config.HISTORY_PATH
  python data_validator.py <csv_path>      # 檢查指定檔案（Dry Run 用）
回傳碼：0 = PASS，1 = FAIL
"""

import csv
import datetime
import os
import sys

import config
from utils.logger import get_logger

log = get_logger("validator")

REQUIRED_FIELDS = ("date", "code")
NUMERIC_FIELDS = ("rsi", "vx", "chg", "ma20_diff", "hi_lo_pos", "close")


def _read(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate(path=None) -> dict:
    """回傳檢查結果 dict（不修改資料）。"""
    path = path or config.HISTORY_PATH
    result = {
        "path": path,
        "total": 0,
        "duplicates": [],
        "non_trading_days": [],
        "missing_values": [],
        "invalid_numeric": [],
        "labeled": 0,
        "passed": False,
    }

    if not os.path.exists(path):
        result["error"] = f"檔案不存在：{path}"
        return result

    rows = _read(path)
    result["total"] = len(rows)

    seen = {}
    for i, r in enumerate(rows, start=2):  # 2 = 含表頭後的實際行號
        date = (r.get("date") or "").strip()
        code = (r.get("code") or "").strip()

        # 1) Duplicate Check
        key = (date, code)
        if key in seen:
            result["duplicates"].append(
                {"row": i, "date": date, "code": code, "first_row": seen[key]}
            )
        else:
            seen[key] = i

        # 2) Trading Day Check
        try:
            if datetime.date.fromisoformat(date).weekday() >= 5:
                result["non_trading_days"].append(
                    {"row": i, "date": date, "code": code, "reason": "non-trading day"}
                )
        except ValueError:
            result["missing_values"].append(
                {"row": i, "field": "date", "value": date, "reason": "invalid date format"}
            )

        # 3) Missing Value Check
        for fld in REQUIRED_FIELDS:
            if not (r.get(fld) or "").strip():
                result["missing_values"].append(
                    {"row": i, "field": fld, "value": "", "reason": "required field empty"}
                )

        # 4) Price / Volume Validation
        for fld in NUMERIC_FIELDS:
            raw = (r.get(fld) or "").strip()
            if raw == "":
                continue  # 空值由 Missing Check 負責，不重複回報
            try:
                v = float(raw)
            except ValueError:
                result["invalid_numeric"].append(
                    {"row": i, "field": fld, "value": raw, "reason": "not a number"}
                )
                continue
            if fld == "rsi" and not (0 <= v <= 100):
                result["invalid_numeric"].append(
                    {"row": i, "field": fld, "value": raw, "reason": "rsi out of range [0,100]"}
                )
            elif fld == "vx" and v <= 0:
                result["invalid_numeric"].append(
                    {"row": i, "field": fld, "value": raw, "reason": "vx must be > 0"}
                )
            elif fld == "close" and v < 0:
                result["invalid_numeric"].append(
                    {"row": i, "field": fld, "value": raw, "reason": "close must be >= 0"}
                )

        if str(r.get("target_label", "")).strip() in ("0", "1"):
            result["labeled"] += 1

    result["passed"] = not (
        result["duplicates"]
        or result["non_trading_days"]
        or result["missing_values"]
        or result["invalid_numeric"]
    )
    return result


def report(res: dict) -> str:
    """產生 DATA CHECK REPORT 文字。"""
    lines = []
    lines.append("=" * 52)
    lines.append("DATA CHECK REPORT")
    lines.append("=" * 52)
    if res.get("error"):
        lines.append(f"ERROR: {res['error']}")
        return "\n".join(lines)

    lines.append(f"File            : {res['path']}")
    lines.append(f"Total rows      : {res['total']}")
    lines.append(f"Labeled samples : {res['labeled']}")
    lines.append("-" * 52)
    lines.append(f"Duplicate keys      : {len(res['duplicates'])}")
    for d in res["duplicates"]:
        lines.append(f"    row {d['row']}: ({d['date']}, {d['code']}) — first at row {d['first_row']}")
    lines.append(f"Non-trading days    : {len(res['non_trading_days'])}")
    for d in res["non_trading_days"]:
        lines.append(f"    row {d['row']}: {d['date']} {d['code']} — {d['reason']}")
    lines.append(f"Missing values      : {len(res['missing_values'])}")
    for d in res["missing_values"]:
        lines.append(f"    row {d['row']}: {d['field']} — {d['reason']}")
    lines.append(f"Invalid numeric     : {len(res['invalid_numeric'])}")
    for d in res["invalid_numeric"]:
        lines.append(f"    row {d['row']}: {d['field']}={d['value']} — {d['reason']}")
    lines.append("-" * 52)
    lines.append(f"RESULT          : {'PASS' if res['passed'] else 'FAIL'}")
    lines.append("=" * 52)
    return "\n".join(lines)


def is_valid(path=None) -> bool:
    """供 Training Gate 呼叫：僅回傳布林，不修改資料。"""
    return validate(path).get("passed", False)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    res = validate(target)
    print(report(res))
    sys.exit(0 if res.get("passed") else 1)
