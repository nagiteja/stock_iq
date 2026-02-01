from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import GeminiError, analyze_stock
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.polygon import PolygonError, TickerNotFoundError

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = await analyze_stock(request.ticker)
    except TickerNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PolygonError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Polygon error while analyzing {request.ticker}: {exc}",
        ) from exc
    except GeminiError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini error while generating report: {exc}",
        ) from exc
    return AnalyzeResponse(**result)
