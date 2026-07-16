# Project Scope — ai-stock-bot

定義各模組的治理層級。Reviewer 只在對應 Scope 內判定；跨層變更需標明並升級審查。

## 層級分類

| 層級 | 模組 |
|---|---|
| **Production** | `main.py`, `scheduler.py`, `config.py`, `core/scanner.py`, `core/filter.py`, `core/scorer.py`, `core/formatter`(push/formatter.py), `push/telegram.py`, `push/line.py`, `.github/workflows/stock.yml`, GAS |
| **Experimental** | `ml/ml_model.py`, `ml/trainer.py`, `ml/backtest_engine.py`, `ml/walkforward.py`, `ml/costs.py` |
| **Infrastructure** | `storage/db.py`, `storage/history.py`, `storage/git_sync.py`, `data_validator.py`, `scripts/clean_history.py` |
| **Documentation** | `README.md`, `docs/`, `docs/governance/` |

## 規則

1. Production 層變更 → 全流程審查（Class A）。
2. Experimental 層變更 → 不得影響 Production 行為。
3. Documentation 層變更 → 免 Python 回歸。
4. 跨層變更 → 以最高層級的流程為準。
