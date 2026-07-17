# AI Analyst Panel — Roadmap

| 版本 | 內容 | 狀態 |
|---|---|---|
| **v1.0** | Technical + Risk 分析、Fundamental SKIPPED、Moderator、Consensus、開關控制 | ✅ 完成 |
| v1.1 | Discussion Engine（分析師互相引用/反駁/修正，非平行評分） | 規劃 |
| v1.2 | Fundamental Provider（接入 EPS/PE/營收 → 啟用 Fundamental） | 規劃 |
| v1.3 | Broker Report Style（券商研究報告式會議結論輸出） | 規劃 |
| v1.4 | Personality Debate（分析師人格化辯論） | 規劃 |

## 重要工程前提（v1.1+ 必須）
Discussion Engine / 人格化 會引入 LLM 生成式文字。依 ENGINEERING_GATES：
**LLM 輸出必須經過「數字白名單閘門」才能進入推播/資料層**——
分析師每句話只能引用系統實算欄位，不得無中生有。此閘門為 v1.1 的前置設計。
