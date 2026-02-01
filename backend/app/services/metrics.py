from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_metrics(
    aggregates: List[Dict[str, Any]], fundamentals: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not aggregates:
        return {}

    df = pd.DataFrame(aggregates)
    if "c" not in df.columns:
        return {}

    df = df.copy()
    df["close"] = pd.to_numeric(df["c"], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("v"), errors="coerce")
    df = df.dropna(subset=["close"])

    if df.empty:
        return {}

    last_close = _safe_float(df["close"].iloc[-1])

    def period_return(days: int) -> Optional[float]:
        if len(df) <= days:
            return None
        start_close = df["close"].iloc[-(days + 1)]
        end_close = df["close"].iloc[-1]
        if start_close == 0 or pd.isna(start_close) or pd.isna(end_close):
            return None
        return float((end_close / start_close) - 1)

    returns = df["close"].pct_change().dropna()
    volatility = float(returns.std() * np.sqrt(252)) if not returns.empty else None

    running_peak = df["close"].cummax()
    drawdown = (df["close"] / running_peak) - 1
    max_drawdown = float(drawdown.min()) if not drawdown.empty else None

    avg_volume = (
        float(df["volume"].dropna().mean())
        if "volume" in df.columns and df["volume"].notna().any()
        else None
    )

    metrics: Dict[str, Any] = {
        "last_close": last_close,
        "return_1m": period_return(21),
        "return_3m": period_return(63),
        "return_6m": period_return(126),
        "volatility_annualized": volatility,
        "max_drawdown": max_drawdown,
        "avg_daily_volume": avg_volume,
    }

    fundamentals = fundamentals or {}
    for key in ["market_cap", "pe_ratio", "eps", "dividend_yield"]:
        if fundamentals.get(key) is not None:
            metrics[key] = fundamentals.get(key)

    return {k: v for k, v in metrics.items() if v is not None}
