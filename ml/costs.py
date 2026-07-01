# -*- coding: utf-8 -*-
"""
ml/costs.py — 台股交易成本模型
================================
回測淨報酬必須扣除成本，否則嚴重高估。
單邊成本：手續費（買賣各一）、證交稅（僅賣出）、滑價（買賣各估）。
所有比率取自 config，可調整。
"""
import config


def round_trip_net(buy: float, sell: float) -> float:
    """單筆來回（買→賣）扣成本後的淨報酬率。

    買進實付 = buy * (1 + fee + slippage)
    賣出實收 = sell * (1 - fee - tax - slippage)
    """
    buy_cost = config.FEE_RATE + config.SLIPPAGE
    sell_cost = config.FEE_RATE + config.TAX_RATE + config.SLIPPAGE
    eff_buy = buy * (1 + buy_cost)
    eff_sell = sell * (1 - sell_cost)
    if eff_buy <= 0:
        return 0.0
    return eff_sell / eff_buy - 1.0


def cost_drag() -> float:
    """單次來回的總成本拖累（近似，供報告顯示）。"""
    return 2 * config.FEE_RATE + config.TAX_RATE + 2 * config.SLIPPAGE
