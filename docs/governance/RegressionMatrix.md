# Regression Matrix

依修改對象決定必驗項目，精準回歸，不必每次盲跑全部。

| 修改對象 | 必驗項目 | 免驗 |
|---|---|---|
| `scheduler.py` | workflow / dispatch / event 解析 / push / logging | — |
| `core/scanner.py` | scorer / filter / history 格式 | — |
| `core/scorer.py`、`core/filter.py` | score 一致性 / history 格式 | — |
| `push/formatter.py` | 推播格式位元級比對 / telegram / line | — |
| `push/telegram.py`、`push/line.py` | 成功判定 / retry / 推播鏈 | — |
| GAS | dispatch 204 / event_type / trigger 建立 | Python 全免 |
| `config.py` | 全模組 import / 門檻讀取 | — |
| `storage/history.py` | 去重 / 寫入格式 / trainer 讀取 | — |
| `README.md` / `docs/` | 無 | **Python 全免** |

## 規則

- 表中未列之新增模組，預設走全回歸（保守）。
- 回歸證據需留檔（git diff / 執行輸出）。
