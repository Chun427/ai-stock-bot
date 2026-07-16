# Review Workflow

## 流程

```
需求
  ↓
Change Classification（判 A / B / C）
  ↓
Risk 分級（P0–P3）
  ├─ Class C / P3 ───────────────→ GPT Supervisor 核准 → Merge
  ├─ Class B ──→ QA → Senior ────→ GPT Supervisor → Merge
  └─ Class A ──→ Architecture → QA → Senior → GPT Supervisor → Merge
                     │FAIL          │FAIL      │
                     ↓              ↓          ↓
                 依 RiskMatrix 處置（P0 停止 / P1 退回）
                                              ↓
                                    RegressionMatrix（精準回歸）
                                              ↓
                                     Merge → 部署後 Regression Test
```

## 固定分工
- **Claude** = 工程師（Architecture Reviewer / QA Reviewer / Senior Engineer 三角色）
- **GPT** = Supervisor（Final Review / Regression / Risk / Merge Decision / Approval）

## 規則
- 任一關 FAIL → 立即停止。
- 全部 PASS 才進下一關。
- 未經 GPT Supervisor Approve，不得修改正式程式碼、不得 Merge。
