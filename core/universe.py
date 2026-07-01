# -*- coding: utf-8 -*-
"""
core/universe.py — 雙層 Universe（依 GPT 監督 P0-2）
=====================================================
Universe A（全市場 / 無動量過濾）：回測用。避免「先漲才進池」的動量偏誤。
Universe B（動量候選）：production 用，即現行 scanner（昨日漲幅榜 top N）。

A 的完整全市場（約 1800 檔）逐檔抓 3–5 年歷史，於 yfinance 既慢又易斷，
故採務實作法：
  1) 優先讀 data/universe.csv（單欄 code，使用者可放完整清單）；
  2) 無檔時用內建「代表性大型/中型權值清單」當樣本（會明確標記非全市場）。
這讓回測「可在任何有網路環境直接執行」，同時不誇稱已涵蓋全市場。
"""
import csv
import os

import config
from utils.logger import get_logger

log = get_logger("universe")

# 內建代表性清單（樣本，非全市場）：跨產業權值股，供無 universe.csv 時可立即回測。
_BUILTIN_SAMPLE = [
    "2330", "2317", "2454", "2308", "2303", "2412", "2882", "2881", "2891", "2886",
    "1301", "1303", "1326", "2002", "2207", "2105", "3008", "2382", "2357", "2409",
    "3711", "2379", "4938", "2474", "2395", "3045", "4904", "2912", "1216", "2801",
    "2880", "2884", "2885", "2890", "2892", "5880", "2603", "2609", "2615", "2618",
]


def production_candidates() -> list:
    """Universe B：動量候選（現行 scanner，production 用）。"""
    from core import scanner
    return scanner.scan()


def backtest_universe() -> list:
    """Universe A：回測用代碼清單。回傳 list[str]（不含市場別）。"""
    path = config.BT_UNIVERSE_CSV
    if os.path.exists(path):
        codes = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if not row:
                        continue
                    c = str(row[0]).strip()
                    if c.isdigit() and len(c) == 4:
                        codes.append(c)
            if codes:
                log.info(f"Universe A 來源：{path}（{len(codes)} 檔，使用者提供）")
                return codes
        except Exception as e:  # noqa: BLE001
            log.warning(f"讀取 universe.csv 失敗，改用內建樣本：{e}")
    log.warning(f"未提供 universe.csv，使用內建代表性樣本 {len(_BUILTIN_SAMPLE)} 檔"
                f"（⚠️ 非全市場，回測結論僅代表此樣本）")
    return list(_BUILTIN_SAMPLE)
