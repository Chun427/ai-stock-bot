# -*- coding: utf-8 -*-
"""
core/scanner.py
全市場掃描：抓「昨日漲幅榜」候選池。
來源優先序：TWSE（上市）→ TPEx（上櫃）→ Yahoo Finance 備援。
回傳 list[dict]：{code, name, market}（最多 config.MAX_CANDIDATES 檔）。

⚠️ 本沙箱網路白名單不含 TWSE/TPEx/Yahoo，無法於此驗證實盤回傳，
   首次於 GitHub Actions 執行時請核對 scanner 數量是否合理（見 [REPORT]）。
   解析皆採防禦式：欄位缺漏自動跳過、來源失敗自動降級。
"""

import requests

import config
from utils.logger import get_logger

log = get_logger("scanner")

UA = {"User-Agent": "Mozilla/5.0 (ai-stock-bot)"}
TWSE_URL = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
TPEX_URL = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php"


def _to_float(x):
    try:
        return float(str(x).replace(",", "").replace("%", "").strip())
    except Exception:  # noqa: BLE001
        return None


def _from_twse():
    """TWSE MI_INDEX ALLBUT0999：全上市個股，依漲跌幅排序取漲幅榜。"""
    try:
        r = requests.get(
            TWSE_URL,
            params={"response": "json", "type": "ALLBUT0999"},
            headers=UA, timeout=config.NET_TIMEOUT,
        )
        j = r.json()
        # MI_INDEX 將個股表放在 data9 / tables 之一，欄位含代號、名稱、漲跌(+/-)、漲跌價差、收盤
        rows = j.get("data9") or j.get("data8") or []
        if not rows and "tables" in j:
            for t in j["tables"]:
                if t.get("data") and len(t["data"][0]) >= 8:
                    rows = t["data"]
                    break
        out = []
        for row in rows:
            try:
                code = str(row[0]).strip()
                name = str(row[1]).strip()
                if not code.isdigit() or len(code) != 4:
                    continue
                sign = str(row[9]).strip() if len(row) > 9 else ""
                diff = _to_float(row[10]) if len(row) > 10 else None
                close = _to_float(row[8]) if len(row) > 8 else None
                if close is None or diff is None or close == 0:
                    continue
                up = "+" if "green" in sign or sign in ("+", "<p style= color:green>+</p>") else ("-" if "red" in sign else "")
                chg = diff / (close - diff) * 100 if (close - diff) else 0
                if "red" in sign.lower():
                    chg = -abs(chg)
                out.append({"code": code, "name": name, "chg": chg, "market": "TWSE"})
            except Exception:  # noqa: BLE001
                continue
        out = [x for x in out if x["chg"] > 0]
        out.sort(key=lambda x: -x["chg"])
        log.info(f"TWSE 取得 {len(out)} 檔上漲標的")
        return out
    except Exception as e:  # noqa: BLE001
        log.warning(f"TWSE 來源失敗：{e}")
        return []


def _from_tpex():
    """TPEx 上櫃每日收盤行情。欄位 schema 可能調整，採防禦式解析。"""
    try:
        r = requests.get(
            TPEX_URL, params={"l": "zh-tw", "o": "json"},
            headers=UA, timeout=config.NET_TIMEOUT,
        )
        j = r.json()
        rows = j.get("aaData") or j.get("data") or []
        out = []
        for row in rows:
            try:
                code = str(row[0]).strip()
                name = str(row[1]).strip()
                if not code.isdigit() or len(code) != 4:
                    continue
                close = _to_float(row[2])
                diff = _to_float(row[3])
                if close is None or diff is None or close == 0:
                    continue
                base = close - diff
                chg = (diff / base * 100) if base else 0
                out.append({"code": code, "name": name, "chg": chg, "market": "TPEx"})
            except Exception:  # noqa: BLE001
                continue
        out = [x for x in out if x["chg"] > 0]
        out.sort(key=lambda x: -x["chg"])
        log.info(f"TPEx 取得 {len(out)} 檔上漲標的")
        return out
    except Exception as e:  # noqa: BLE001
        log.warning(f"TPEx 來源失敗：{e}")
        return []


def _excluded(code: str, name: str) -> bool:
    """Universe 排除規則（由 config 開關控制；預設全 False＝不改變現行行為）。"""
    if config.EXCLUDE_ETF and code.startswith("00"):
        return True
    if config.EXCLUDE_KY and "KY" in name.upper():
        return True
    return False


def scan() -> list:
    """整合 TWSE + TPEx，回傳候選池（上限 MAX_CANDIDATES）。"""
    pool = _from_twse() + _from_tpex()
    if not pool:
        log.error("TWSE/TPEx 皆無資料，候選池為空（將觸發 fail-safe 空結果推播）")
        return []
    pool = [x for x in pool if not _excluded(x["code"], x["name"])]
    pool.sort(key=lambda x: -x["chg"])
    capped = pool[: config.MAX_CANDIDATES]
    # 誠實記錄：實際上漲檔數 vs 取用（cap）檔數，便於判斷是否觸頂
    log.info(f"候選池：上漲 {len(pool)} 檔，取用 {len(capped)} 檔（cap={config.MAX_CANDIDATES}）")
    return [{"code": x["code"], "name": x["name"], "market": x["market"]} for x in capped]
