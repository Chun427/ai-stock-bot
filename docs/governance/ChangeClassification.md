# Change Classification

依變更範圍決定必經流程，避免所有修改都走同一條重流程。

| Class | 範圍 | 必經流程 |
|---|---|---|
| **Class A** | Production / Architecture / Workflow / Scheduler / Scanner / Filter / Scorer / Formatter / GAS | Architecture → QA → Senior Engineer → GPT Supervisor |
| **Class B** | Business Logic / Experimental（ml, backtest） | QA → Senior Engineer → GPT Supervisor |
| **Class C** | Documentation | GPT Supervisor 核准即可 |

## 規則

- 一個變更同時觸及多 Class → 以最高 Class（A > B > C）為準。
- Class 由 Architecture Reviewer 於流程起點判定。
