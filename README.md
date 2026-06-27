# 🤖 台股全市場 AI 選股系統 · ai-stock-bot

每日自動掃描上市＋上櫃全市場，結合技術分析、歷史回測勝率與機器學習評分，
透過 LINE Messaging API / Telegram Bot 推播精選潛力股。模型每週五自動重訓。

## 執行排程（UTC cron）

| 台灣時間 | cron | MODE | 說明 |
|---|---|---|---|
| 09:00 | `0 1 * * 1-5` | `morning` | 掃描 → 技術+ML 評分 → 推播前 5 名，特徵寫入 history.csv |
| 14:45 | `45 6 * * 1-4` | `verify` | 驗證已達 5 交易日之預測 → 5 日波段標記 → 回填標籤 → 推播 |
| 14:50（五）| `50 6 * * 5` | `weekly` | 當日驗證 + 週報 + 重訓 ML + 回測報告 |
| 手動 | — | `test` | 推播測試訊息，確認 Token 與管道 |

MODE 由 workflow 依 cron 寫入 `$GITHUB_ENV`；非白名單值 Python 端 fallback 為 `morning`。

## GitHub Secrets

| 名稱 | 說明 | 必填 |
|---|---|---|
| `LINE_TOKEN` | LINE Channel Access Token | 擇一 |
| `LINE_ID` | 推播目標 User ID | 擇一 |
| `TG_TOKEN` | Telegram Bot Token | 擇一 |
| `TG_CHAT` | Telegram Chat ID（群組以 `-100` 開頭）| 擇一 |

> Settings → Actions → General → Workflow permissions 須設為 **Read and write**，
> 讓 Actions 能 commit `db.json` / `history.csv` / `model.pkl` 回 repo。

## 5 日波段標記規則

- 買入後最多 5 個交易日，任一日 High 漲幅 > **+3%** 且未先觸停損 → 命中（label=1）
- 期間任一日 Low 跌幅 ≤ **-1.5%** → 強制失敗（label=0，即使後來漲回）
- 結果回填 `history.csv` 之 `target_label`，作為 ML 訓練標籤

## ML 模型

- RandomForestClassifier（100 棵、max_depth=5）
- 特徵：rsi, vx, chg, ma20_diff, hi_lo_pos, weekday
- 最低訓練門檻 30 筆有標籤樣本；不足時純 Rule-based，推播不中斷
- 週五 TimeSeriesSplit×5 回測（no shuffle，防未來資料洩露）

## 檔案結構

```
main.py            MODE 分派 + [REPORT]
config.py          環境變數 / 常數 / 路徑
core/              scanner filter scorer verifier market_data weekly_report
ml/                ml_model trainer backtest
push/              formatter(契約) telegram line
storage/           db history git_sync
utils/             logger
data/              db.json history.csv model.pkl(自動生成)
.github/workflows/ stock.yml
```

## 推播格式契約

所有推播字串唯一定義於 `push/formatter.py`，頂部 4 個 CONTRACT TOGGLES
對應 README 與螢幕的歧異（早盤標題 / 驗證邊框 / 半形括號 / 內層標題），改一行即可鎖定。

## 免責聲明

本系統僅供學習研究，選股結果不構成投資建議。投資有風險，請自行評估。
