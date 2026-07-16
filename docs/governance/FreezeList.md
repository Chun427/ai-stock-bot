# Freeze List

凍結區清單。標示各檔案的可變更程度。

| 凍結等級 | 檔案 | 規則 |
|---|---|---|
| **Production Freeze** | `scheduler.py`, `.github/workflows/stock.yml`, `main.py`, `core/scanner.py`, `core/filter.py`, `core/scorer.py`, `push/formatter.py`, GAS | 非雙 Reviewer（Architecture + QA）提出相同缺陷，不得修改 |
| **Semi Freeze** | `config.py`, `README.md` | 需 Architecture Reviewer 核准後方可改 |
| **Open** | `docs/`, `docs/governance/`, `scripts/`（一次性工具）, tests/ | 一般流程即可 |

## 規則

- Production Freeze 檔案的變更一律 Class A。
- 凍結區的「契約」（event_type、推播格式、門檻語意）視為不可變 API。
