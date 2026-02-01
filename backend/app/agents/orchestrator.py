from __future__ import annotations

import json
from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from google.adk.agents import Agent
    from app.services.polygon import PolygonData
from pydantic import BaseModel, ValidationError

from app.agents.prompts import (
    ANALYSIS_PROMPT,
    COMPILER_PROMPT,
    FUNDAMENTAL_PROMPT,
    SCORE_PROMPT,
    TECHNICAL_PROMPT,
)
from app.core.config import GEMINI_API_KEY
from app.models.schemas import (
    CompilerScorecard,
    FundamentalScorecard,
    Scorecard,
    TechnicalScorecard,
)


class GeminiError(Exception):
    pass


logger = logging.getLogger(__name__)


def _build_agent(name: str, output_schema: Optional[Type[BaseModel]] = None) -> "Agent":
    if not GEMINI_API_KEY:
        raise GeminiError("GEMINI_API_KEY is not set.")

    from google.adk.agents import Agent
    from google.adk.models.google_llm import Gemini
    from google.genai import types

    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )

    return Agent(
        name=name,
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config,
        ),
        description="Single-stock investor-style analysis agent.",
        instruction="Follow the system prompt exactly.",
        output_schema=output_schema,
    )


def _content_to_text(content: Any | None) -> str:
    if not content or not content.parts:
        return ""
    parts: List[str] = []
    for part in content.parts:
        if part.text:
            parts.append(part.text)
    return "".join(parts).strip()


def _truncate_text(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...[truncated]"


def _extract_final_text(events: List[Any]) -> str:
    for event in reversed(events):
        if getattr(event, "author", "") != "user" and event.is_final_response():
            text = _content_to_text(event.content)
            if text:
                return text
    return ""


def _format_timestamp(ts: Any) -> str:
    try:
        return datetime.fromtimestamp(float(ts) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return "unknown date"


def _format_price_summary(aggregates: List[Dict[str, Any]]) -> str:
    if not aggregates:
        return "No recent price aggregates available."
    first = aggregates[0]
    last = aggregates[-1]
    return (
        f"From {_format_timestamp(first.get('t'))} to {_format_timestamp(last.get('t'))}, "
        f"close moved from {first.get('c')} to {last.get('c')}."
    )


def _normalize_price_data(price_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for bar in price_data or []:
        if not isinstance(bar, dict):
            continue
        normalized.append(
            {
                "time": bar.get("time", bar.get("t")),
                "open": bar.get("open", bar.get("o")),
                "high": bar.get("high", bar.get("h")),
                "low": bar.get("low", bar.get("l")),
                "close": bar.get("close", bar.get("c")),
                "volume": bar.get("volume", bar.get("v")),
            }
        )
    return normalized


async def _run_agent(
    prompt: str,
    name: str,
    output_schema: Optional[Type[BaseModel]] = None,
) -> str:
    start = time.perf_counter()
    logger.info("Agent start: %s", name)
    agent = _build_agent(name, output_schema=output_schema)
    from google.adk.runners import InMemoryRunner

    runner = InMemoryRunner(agent=agent)
    try:
        events = await runner.run_debug(prompt, quiet=True)
        response_text = _extract_final_text(events)
        if not response_text:
            raise GeminiError("Gemini did not return a usable response.")
        logger.info(
            "Agent done: %s (%.2fs)", name, time.perf_counter() - start
        )
        return response_text
    except Exception as exc:
        logger.exception(
            "Agent failed: %s (%.2fs)", name, time.perf_counter() - start
        )
        raise exc


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise GeminiError("Scoring agent did not return a JSON object.")
    return text[start : end + 1]


def _parse_scorecard(text: str) -> Dict[str, Any]:
    try:
        return Scorecard.model_validate_json(text).model_dump()
    except ValidationError:
        try:
            logger.debug(
                "Score agent raw response (truncated): %s",
                _truncate_text(text),
            )
            raw_json = _extract_json_object(text)
            return Scorecard.model_validate_json(raw_json).model_dump()
        except ValidationError as exc:
            logger.debug(
                "Score agent JSON response (truncated): %s",
                _truncate_text(raw_json),
            )
            raise GeminiError("Scoring agent did not return valid JSON.") from exc


async def analyze_score(
    ticker: str,
    as_of: str,
    company_json: Dict[str, Any],
    price_summary: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = SCORE_PROMPT.format(
        ticker=ticker,
        as_of=as_of,
        company_json=json.dumps(company_json or {}, ensure_ascii=True),
        price_summary=price_summary,
        metrics_json=json.dumps(metrics or {}, ensure_ascii=True),
    )
    response = await _run_agent(prompt, "score_agent", output_schema=Scorecard)
    return _parse_scorecard(response)


def _parse_technical_scorecard(text: str) -> Dict[str, Any]:
    try:
        return TechnicalScorecard.model_validate_json(text).model_dump()
    except ValidationError:
        try:
            logger.debug(
                "Technical agent raw response (truncated): %s",
                _truncate_text(text),
            )
            return TechnicalScorecard.model_validate_json(
                _extract_json_object(text)
            ).model_dump()
        except ValidationError as exc:
            raise GeminiError("Technical agent did not return valid JSON.") from exc


def _parse_fundamental_scorecard(text: str) -> Dict[str, Any]:
    try:
        return FundamentalScorecard.model_validate_json(text).model_dump()
    except ValidationError:
        try:
            logger.debug(
                "Fundamental agent raw response (truncated): %s",
                _truncate_text(text),
            )
            return FundamentalScorecard.model_validate_json(
                _extract_json_object(text)
            ).model_dump()
        except ValidationError as exc:
            raise GeminiError("Fundamental agent did not return valid JSON.") from exc


def _parse_compiler_scorecard(text: str) -> Dict[str, Any]:
    try:
        return CompilerScorecard.model_validate_json(text).model_dump()
    except ValidationError:
        try:
            logger.debug(
                "Compiler agent raw response (truncated): %s",
                _truncate_text(text),
            )
            return CompilerScorecard.model_validate_json(
                _extract_json_object(text)
            ).model_dump()
        except ValidationError as exc:
            raise GeminiError("Compiler agent did not return valid JSON.") from exc


async def analyze_technical(
    ticker: str,
    as_of: str,
    price_data: List[Dict[str, Any]],
    indicators: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    prompt = TECHNICAL_PROMPT.format(
        ticker=ticker,
        as_of=as_of,
        price_data_json=json.dumps(_normalize_price_data(price_data), ensure_ascii=True),
        indicators_json=json.dumps(indicators or {}, ensure_ascii=True),
    )
    response = await _run_agent(prompt, "technical_agent", output_schema=TechnicalScorecard)
    return _parse_technical_scorecard(response)


async def analyze_fundamental(
    ticker: str,
    as_of: str,
    company_json: Dict[str, Any],
    financials: Optional[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = FUNDAMENTAL_PROMPT.format(
        ticker=ticker,
        as_of=as_of,
        company_json=json.dumps(company_json or {}, ensure_ascii=True),
        financials_json=json.dumps(financials or {}, ensure_ascii=True),
        metrics_json=json.dumps(metrics or {}, ensure_ascii=True),
    )
    response = await _run_agent(
        prompt, "fundamental_agent", output_schema=FundamentalScorecard
    )
    return _parse_fundamental_scorecard(response)


async def analyze_compiler(
    ticker: str,
    as_of: str,
    technical_result: Dict[str, Any],
    fundamental_result: Dict[str, Any],
    weights: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    prompt = COMPILER_PROMPT.format(
        ticker=ticker,
        as_of=as_of,
        technical_json=json.dumps(technical_result or {}, ensure_ascii=True),
        fundamental_json=json.dumps(fundamental_result or {}, ensure_ascii=True),
        weights_json=json.dumps(weights or {}, ensure_ascii=True),
    )
    response = await _run_agent(prompt, "compiler_agent", output_schema=CompilerScorecard)
    return _parse_compiler_scorecard(response)


async def analyze_stock(ticker: str) -> Dict[str, Any]:
    overall_start = time.perf_counter()
    logger.info("Analyze start: %s", ticker)
    from app.services.metrics import compute_metrics
    from app.services.polygon import fetch_polygon_data

    polygon_data: "PolygonData" = fetch_polygon_data(ticker)
    metrics = compute_metrics(polygon_data.aggregates, polygon_data.financials)
    as_of = datetime.now(timezone.utc).isoformat()
    price_summary = _format_price_summary(polygon_data.aggregates)

    prompt = ANALYSIS_PROMPT.format(
        ticker=ticker,
        as_of=as_of,
        company_json=json.dumps(polygon_data.company, ensure_ascii=True),
        price_summary=price_summary,
        metrics_json=json.dumps(metrics, ensure_ascii=True),
    )

    report_markdown = await _run_agent(prompt, "analysis_agent")
    scorecard = await analyze_score(
        ticker=ticker,
        as_of=as_of,
        company_json=polygon_data.company,
        price_summary=price_summary,
        metrics=metrics,
    )

    technical_result = await analyze_technical(
        ticker=ticker,
        as_of=as_of,
        price_data=polygon_data.aggregates,
        indicators={},
    )
    fundamental_result = await analyze_fundamental(
        ticker=ticker,
        as_of=as_of,
        company_json=polygon_data.company,
        financials=polygon_data.financials,
        metrics=metrics,
    )
    compiler_result = await analyze_compiler(
        ticker=ticker,
        as_of=as_of,
        technical_result=technical_result,
        fundamental_result=fundamental_result,
    )

    result = {
        "ticker": ticker,
        "report_markdown": report_markdown,
        "metrics": metrics,
        "scorecard": scorecard,
        "compiler_scorecard": compiler_result,
        "as_of": as_of,
    }
    logger.info(
        "Analyze done: %s (%.2fs)", ticker, time.perf_counter() - overall_start
    )
    return result
