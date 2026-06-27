# -*- coding: utf-8 -*-
"""
storage/git_sync.py
將狀態檔（db.json / history.csv / model.pkl）commit + push 回 repo。
- 僅在 GitHub Actions 環境（GITHUB_ACTIONS=='true'）執行 push；本機為 no-op
- 以 github-actions[bot] 身分提交
- 無變更時安全略過（避免 exit 128：先 `git add` 再 `git diff --cached --quiet` 判斷）
- 任何步驟失敗皆攔截，不中斷主流程
這是過去 P0（morning/verify 未寫回狀態）的關鍵防線，三種模式都應呼叫。
"""

import os
import subprocess

import config
from utils.logger import get_logger

log = get_logger("git_sync")

BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"

# 需要追蹤回寫的狀態檔
TRACK_FILES = [config.DB_PATH, config.HISTORY_PATH, config.MODEL_PATH]


def _run(args: list) -> tuple:
    p = subprocess.run(args, cwd=config.BASE_DIR,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def commit_state(message: str) -> str:
    """回傳 'success' / 'fail' / 'n/a'（無變更或非 CI 環境）。"""
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        log.info("非 GitHub Actions 環境，略過 commit（n/a）")
        return "n/a"

    try:
        _run(["git", "config", "user.name", BOT_NAME])
        _run(["git", "config", "user.email", BOT_EMAIL])

        # 只 add 存在的狀態檔
        existing = [f for f in TRACK_FILES if os.path.exists(f)]
        if not existing:
            log.info("無狀態檔可提交（n/a）")
            return "n/a"
        _run(["git", "add"] + existing)

        # 無 staged 變更 → 安全略過（避免 exit 128）
        code, _ = _run(["git", "diff", "--cached", "--quiet"])
        if code == 0:
            log.info("狀態無變更，略過 commit（n/a）")
            return "n/a"

        code, out = _run(["git", "commit", "-m", message])
        if code != 0:
            log.error(f"commit 失敗：{out}")
            return "fail"

        code, out = _run(["git", "push"])
        if code != 0:
            log.error(f"push 失敗：{out}")
            return "fail"

        log.ok("狀態已 commit + push 回 repo")
        return "success"
    except Exception as e:  # noqa: BLE001
        log.error(f"git_sync 例外：{e}")
        return "fail"
