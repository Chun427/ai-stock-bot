# -*- coding: utf-8 -*-
"""
ml/backtest.py
TimeSeriesSplit × 5 回測（禁止 shuffle，防未來資料洩露）。
回傳 dict：n_samples, base_winrate, avg_acc, avg_auc, feat_importance
資料不足或失敗回 None。
"""

import config
from utils.logger import get_logger
from storage import history

log = get_logger("backtest")


def run():
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

    n = len(y)
    if n < config.ML_MIN_LABELS or len(set(y)) < 2:
        log.warning(f"樣本不足或單一類別（n={n}），略過回測")
        return None

    try:
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.metrics import accuracy_score, roc_auc_score

        X = np.array(X)
        y = np.array(y)
        tscv = TimeSeriesSplit(n_splits=5)
        accs, aucs = [], []
        last_clf = None

        for tr, te in tscv.split(X):
            if len(set(y[tr])) < 2:
                continue
            clf = RandomForestClassifier(
                n_estimators=config.ML_N_ESTIMATORS,
                max_depth=config.ML_MAX_DEPTH,
                random_state=42,
            )
            clf.fit(X[tr], y[tr])
            last_clf = clf
            pred = clf.predict(X[te])
            accs.append(accuracy_score(y[te], pred))
            try:
                proba = clf.predict_proba(X[te])[:, 1]
                if len(set(y[te])) > 1:
                    aucs.append(roc_auc_score(y[te], proba))
            except Exception:  # noqa: BLE001
                pass

        if not accs or last_clf is None:
            log.warning("回測無有效折，略過")
            return None

        importance = {
            f: round(float(imp), 2)
            for f, imp in zip(config.ML_FEATURES, last_clf.feature_importances_)
        }
        return {
            "n_samples": n,
            "base_winrate": round(float(np.mean(y)) * 100, 1),
            "avg_acc": round(float(np.mean(accs)) * 100, 1),
            "avg_auc": round(float(np.mean(aucs)) * 100, 1) if aucs else 0.0,
            "feat_importance": importance,
        }
    except Exception as e:  # noqa: BLE001
        log.error(f"回測失敗：{e}")
        return None
