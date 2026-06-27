# -*- coding: utf-8 -*-
"""
ml/ml_model.py
模型載入與評分。
- 載入 data/model.pkl
- predict_proba → 0~10 分（未來 5 日波段獲利機率 × 10）
- 無模型或任何錯誤 → 回傳 None（呼叫端 fallback 純 Rule-based，推播不中斷）
"""

import os

import config
from utils.logger import get_logger

log = get_logger("ml_model")

_model = None
_loaded = False


def load():
    global _model, _loaded
    if _loaded:
        return _model
    _loaded = True
    if not os.path.exists(config.MODEL_PATH):
        log.info("model.pkl 不存在，使用純 Rule-based 模式")
        return None
    try:
        import joblib
        _model = joblib.load(config.MODEL_PATH)
        log.ok("model.pkl 載入成功")
    except Exception as e:  # noqa: BLE001
        log.warning(f"model.pkl 載入失敗，fallback Rule-based：{e}")
        _model = None
    return _model


def predict_score(feat: dict):
    """回傳 0~10 float 或 None。"""
    model = load()
    if model is None or not feat:
        return None
    try:
        x = [[float(feat.get(k, 0)) for k in config.ML_FEATURES]]
        proba = model.predict_proba(x)[0]
        # 取「上漲(label=1)」機率
        classes = list(getattr(model, "classes_", [0, 1]))
        idx = classes.index(1) if 1 in classes else (len(proba) - 1)
        p = float(proba[idx])
        return round(p * 10.0, 1)
    except Exception as e:  # noqa: BLE001
        log.warning(f"預測失敗，fallback：{e}")
        return None
