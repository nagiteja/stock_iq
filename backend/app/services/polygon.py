from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import POLYGON_API_KEY

POLYGON_BASE_URL = "https://api.polygon.io"


class PolygonError(Exception):
    pass


class TickerNotFoundError(PolygonError):
    pass


@dataclass
class PolygonData:
    company: Dict[str, Any]
    aggregates: List[Dict[str, Any]]
    financials: Optional[Dict[str, Any]]


def _request_json(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not POLYGON_API_KEY:
        raise PolygonError("POLYGON_API_KEY is not set.")
    import requests

    url = f"{POLYGON_BASE_URL}{path}"
    params = params or {}
    params["apiKey"] = POLYGON_API_KEY
    response = requests.get(url, params=params, timeout=20)
    if response.status_code != 200:
        raise PolygonError(
            f"Polygon request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def fetch_company_details(ticker: str) -> Dict[str, Any]:
    data = _request_json(f"/v3/reference/tickers/{ticker}")
    results = data.get("results")
    if not results:
        raise TickerNotFoundError(f"Ticker '{ticker}' not found on Polygon.")
    company = {
        "ticker": results.get("ticker"),
        "name": results.get("name"),
        "description": results.get("description"),
        "market_cap": results.get("market_cap"),
        "primary_exchange": results.get("primary_exchange"),
        "sic_description": results.get("sic_description"),
        "homepage_url": results.get("homepage_url"),
    }
    return {k: v for k, v in company.items() if v is not None}


def fetch_daily_aggregates(ticker: str, trading_days: int = 180) -> List[Dict[str, Any]]:
    end_date = date.today()
    start_date = end_date - timedelta(days=max(270, trading_days * 2))
    data = _request_json(
        f"/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}",
        params={
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
        },
    )
    results = data.get("results")
    if not results:
        raise TickerNotFoundError(
            f"No aggregate data found for ticker '{ticker}'."
        )
    return results[-trading_days:]


def fetch_latest_financials(ticker: str) -> Optional[Dict[str, Any]]:
    try:
        data = _request_json(
            "/vX/reference/financials",
            params={"ticker": ticker, "limit": 1, "sort": "filing_date", "order": "desc"},
        )
    except PolygonError:
        return None

    results = data.get("results")
    if not results:
        return None

    result = results[0]
    metrics = result.get("metrics") or {}
    financials = {
        "market_cap": result.get("market_cap") or metrics.get("market_cap"),
        "pe_ratio": metrics.get("price_to_earnings_ratio"),
        "eps": metrics.get("earnings_per_share"),
        "dividend_yield": metrics.get("dividend_yield"),
    }
    return {k: v for k, v in financials.items() if v is not None}


def fetch_polygon_data(ticker: str) -> PolygonData:
    company = fetch_company_details(ticker)
    aggregates = fetch_daily_aggregates(ticker)
    financials = fetch_latest_financials(ticker)
    return PolygonData(company=company, aggregates=aggregates, financials=financials)
