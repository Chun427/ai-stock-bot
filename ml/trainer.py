# -*- coding: utf-8 -*-
"""
ml/trainer.py
重訓 RandomForest 並輸出 data/model.pkl。
- 需 ≥ config.ML_MIN_LABELS 筆有標籤(0/1)樣本，否則不訓練（回傳 None）
- 特徵：config.ML_FEATURES；目標：target_label
- commit 由上層 git_sync 處理（本檔只負責產出檔案）
"""

import config
from utils.logger import get_logger
from storage import history

log = get_logger("trainer")


def _load_xy():
    rows = history.read_all()
    X, y = [], []
    for r in rows:
        lab = str(r.get("target_label", "")).strip()
        if lab not in ("0", "1"):
            continue
        try:
            X.append([float(r.get(k, 0) or 0) for k in config.ML_FEATURES])
            y.append(int(lab))
        except Exception:  # noqa: BLE001
            continue
    return X, y


def train():
    """回傳訓練後的 model 或 None。"""
    X, y = _load_xy()
    n = len(y)
    if n < config.ML_MIN_LABELS:
        log.warning(f"有標籤樣本僅 {n} 筆（<{config.ML_MIN_LABELS}），暫不訓練")
        return None
    if len(set(y)) < 2:
        log.warning("標籤僅單一類別，無法訓練")
        return None
    try:
        from sklearn.ensemble import RandomForestClassifier
        import joblib

        clf = RandomForestClassifier(
            n_estimators=config.ML_N_ESTIMATORS,
            max_depth=config.ML_MAX_DEPTH,
            random_state=42,
        )
        clf.fit(X, y)
        joblib.dump(clf, config.MODEL_PATH)
        log.ok(f"模型重訓完成（樣本 {n} 筆），已輸出 model.pkl")
        return clf
    except Exception as e:  # noqa: BLE001
        log.error(f"重訓失敗：{e}")
        return None
