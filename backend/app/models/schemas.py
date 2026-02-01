import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        ticker = value.strip().upper()
        if not re.fullmatch(r"[A-Z.\-]{1,10}", ticker):
            raise ValueError(
                "Ticker must be 1-10 characters and contain only letters, '.' or '-'."
            )
        return ticker


class AnalyzeResponse(BaseModel):
    ticker: str
    report_markdown: str
    metrics: Dict[str, Any]
    scorecard: Dict[str, Any]
    compiler_scorecard: Optional[Dict[str, Any]] = None
    as_of: str


class Scorecard(BaseModel):
    score: int = Field(..., ge=0, le=100)
    short_term: Literal["Buy", "Not Buy"]
    mid_term: Literal["Buy", "Not Buy"]
    long_term: Literal["Buy", "Not Buy"]
    rationale: str


class TechnicalTimeframe(BaseModel):
    trend: Literal["up", "down", "sideways"]
    notes: str


class TechnicalTimeframes(BaseModel):
    short_term: TechnicalTimeframe
    medium_term: TechnicalTimeframe
    long_term: TechnicalTimeframe


class TechnicalKeyLevels(BaseModel):
    support: List[float] = Field(..., min_length=2, max_length=2)
    resistance: List[float] = Field(..., min_length=2, max_length=2)


class TechnicalScorecard(BaseModel):
    agent: Literal["technical"]
    ticker: str
    as_of: str
    score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    signal: Literal["strong_buy", "buy", "neutral", "sell", "strong_sell"]
    timeframes: TechnicalTimeframes
    key_levels: TechnicalKeyLevels
    reasons: List[str] = Field(..., min_length=3, max_length=6)
    risks: List[str] = Field(..., min_length=1, max_length=3)


class FundamentalQuality(BaseModel):
    profitability: int = Field(..., ge=0, le=100)
    growth: int = Field(..., ge=0, le=100)
    balance_sheet: int = Field(..., ge=0, le=100)
    cash_flow: int = Field(..., ge=0, le=100)
    valuation: int = Field(..., ge=0, le=100)


class FundamentalScorecard(BaseModel):
    agent: Literal["fundamental"]
    ticker: str
    as_of: str
    score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    signal: Literal["strong_buy", "buy", "neutral", "sell", "strong_sell"]
    quality: FundamentalQuality
    reasons: List[str] = Field(..., min_length=3, max_length=6)
    risks: List[str] = Field(..., min_length=1, max_length=3)


class CompilerWeights(BaseModel):
    technical: float
    fundamental: float


class CompilerComponent(BaseModel):
    score: int = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    signal: str
    highlights: List[str] = Field(..., min_length=2, max_length=2)


class CompilerComponents(BaseModel):
    technical: CompilerComponent
    fundamental: CompilerComponent


class CompilerScorecard(BaseModel):
    ticker: str
    as_of: str
    weights: CompilerWeights
    final_score: int = Field(..., ge=0, le=100)
    final_confidence: float = Field(..., ge=0, le=1)
    final_signal: Literal["strong_buy", "buy", "neutral", "sell", "strong_sell"]
    components: CompilerComponents
    top_reasons: List[str] = Field(..., min_length=2, max_length=4)
    key_risks: List[str] = Field(..., min_length=1, max_length=3)


class ErrorResponse(BaseModel):
    detail: str
