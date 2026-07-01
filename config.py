# -*- coding: utf-8 -*-
"""
config.py
集中管理：環境變數、常數、檔案路徑、MODE 白名單。
所有 Token 一律 .strip() 去除隱形換行符。
本檔不含任何業務邏輯，僅供讀取設定。
"""

import os

# ============================================================
# 環境變數（Secrets）— 一律 strip 去除隱形換行
# ============================================================
def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key, default) or "").strip()


LINE_TOKEN = _env("LINE_TOKEN")
LINE_ID = _env("LINE_ID")
TG_TOKEN = _env("TG_TOKEN")
TG_CHAT = _env("TG_CHAT")

# MODE 白名單，非法值 fallback 為 morning（確保不靜默終止）
# 單一來源：由 scheduler.py 定義（避免雙頭維護）
from scheduler import VALID_MODES as _VALID_MODES, FALLBACK_MODE as _FALLBACK
_raw_mode = _env("MODE", _FALLBACK)
MODE = _raw_mode if _raw_mode in _VALID_MODES else _FALLBACK
MODE_FALLBACK_USED = _raw_mode not in _VALID_MODES

# ============================================================
# 檔案路徑
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "db.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.csv")
MODEL_PATH = os.path.join(DATA_DIR, "model.pkl")

# ============================================================
# 掃描 / 候選池
# ============================================================
MAX_CANDIDATES = 230          # 候選池上限（★ 這是「上限/cap」，非實際全市場檔數）
TOP_N = 5                     # 最終推播檔數
HISTORY_DAYS = 62             # 個股回測歷史天數

# ── Universe Definition（明確排除規則；預設維持現行行為，改 True 才生效）──
# 現行 universe = TWSE上市 + TPEx上櫃，4 位數字代號，昨日上漲，依漲幅取前 MAX_CANDIDATES。
EXCLUDE_ETF = False           # True 則排除 00 開頭 ETF（如 0050/0056/00878）
EXCLUDE_KY = False            # True 則排除 -KY 外國企業（如 臻鼎-KY 4958）
# 註：權證/牛熊證（非 4 位數字代號）已天然排除；興櫃不在資料來源內亦排除。
#     處置股/停牌/全額交割「目前未明確排除」（資料來源未標記），列為已知風險。

# ============================================================
# 技術濾網
# ============================================================
RSI_MIN = 40.0
RSI_MAX = 82.0
RSI_PERIOD = 14
MA_PERIOD = 20
VOL_RATIO_MIN = 1.0           # 成交量比下限（當日量 / 近期均量）

# ============================================================
# 回測評分 / 樣本數權重
# ============================================================
def sample_weight(n: int) -> float:
    """樣本數越少權重越低，避免新上市 ETF 假勝率。"""
    if n >= 25:
        return 1.0
    if n >= 15:
        return 0.8
    if n >= 5:
        return 0.5
    return 0.0  # <5 筆排除

# ============================================================
# 5 日波段驗證標記
# ============================================================
VERIFY_WINDOW = 5             # 未來交易日數
HIT_THRESHOLD = 0.03          # 任一日 High 漲幅 > +3% → 命中
STOP_THRESHOLD = -0.015       # 任一日 Low 跌幅 ≤ -1.5% → 強制失敗

# ============================================================
# 美股連動判斷
# ============================================================
US_INDEX = "^GSPC"            # 內部抓取用；推播顯示為 SPY
US_QQQ = "QQQ"
US_CRASH_THRESHOLD = -0.005   # 兩者皆 ≤ -0.5% → 暫停選股

# ============================================================
# ML 模型
# ============================================================
ML_MIN_LABELS = 30            # 最低訓練門檻（有標籤樣本數）
ML_N_ESTIMATORS = 100
ML_MAX_DEPTH = 5
ML_FEATURES = ["rsi", "vx", "chg", "ma20_diff", "hi_lo_pos", "weekday"]

# ============================================================
# 推播
# ============================================================
TG_MAX_LEN = 4096            # Telegram 單則上限
TG_RETRY = 4
LINE_RETRY = 3
NET_TIMEOUT = 15             # 單次網路請求 timeout（秒）— 修正 yfinance 無 timeout 風險

# history.csv 欄位（特徵 + 標籤）
HISTORY_HEADER = [
    "date", "code", "name", "rsi", "vx", "chg",
    "ma20_diff", "hi_lo_pos", "weekday", "target_label",
]

# ============================================================
# Backtest Mode（投資有效性驗證；功能凍結後唯一新增能力）
# ============================================================
# 台股交易成本（單邊比率）— 用於回測淨報酬，避免過度樂觀
FEE_RATE = 0.001425          # 券商手續費（買、賣各一次）
TAX_RATE = 0.003             # 證交稅（僅賣出）
SLIPPAGE = 0.001             # 滑價（買、賣各估一次；可調）

# 回測參數
BT_HOLD_DAYS = VERIFY_WINDOW # 持有交易日（與線上策略一致＝5）
BT_TOP_N = TOP_N             # 每期選股數＝5
BT_YEARS = 4                 # 預設回測年數（抓 yfinance 歷史）
BT_INDEX_TICKER = "0050.TW"  # 大盤買進持有基準（元大台灣50）
BT_RANDOM_SEED = 42
# 回測 universe 來源：優先讀 data/universe.csv（單欄 code），無則用內建代表性清單
BT_UNIVERSE_CSV = os.path.join(DATA_DIR, "universe.csv")
BT_OUTPUT_DIR = os.path.join(DATA_DIR, "backtests")
