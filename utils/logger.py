# -*- coding: utf-8 -*-
"""
utils/logger.py
統一 log 格式：[模組] 訊息
不依賴 logging 設定檔，直接 print，確保 GitHub Actions log 必定可見。
"""

import sys


class Logger:
    def __init__(self, module: str):
        self.module = module

    def _emit(self, level: str, msg: str):
        line = f"[{self.module}] {msg}"
        # error 走 stderr，其餘走 stdout；GitHub Actions 兩者皆收
        stream = sys.stderr if level == "error" else sys.stdout
        print(line, file=stream, flush=True)

    def info(self, msg: str):
        self._emit("info", msg)

    def warning(self, msg: str):
        self._emit("warning", f"⚠️ {msg}")

    def error(self, msg: str):
        self._emit("error", f"❌ {msg}")

    def ok(self, msg: str):
        self._emit("info", f"✅ {msg}")


def get_logger(module: str) -> Logger:
    return Logger(module)
