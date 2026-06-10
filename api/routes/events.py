from fastapi import APIRouter, Query
from data.loader import get_data
from data.preprocessor import build_features
from events.analyzer import run_event_study, summarise_study
from events.live_fetcher import get_events, invalidate_cache, fetch_live_events

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/calendar")
def list_events(category: str = Query(None)):
    """Return all macro events, fetched live from FRED (cached 6h)."""
    return get_events(category)


@router.get("/refresh")
def refresh_events():
    """Invalidate the event cache and re-fetch from FRED immediately."""
    invalidate_cache()
    events = fetch_live_events()
    return {"status": "ok", "event_count": len(events)}


@router.get("/study")
def event_study(
    ticker:   str = Query("^GSPC"),
    period:   str = Query("5y"),
    window:   int = Query(10),
    category: str = Query(None),
):
    df = build_features(get_data(ticker, period))
    events = get_events(category)
    results = run_event_study(df, window, events)
    summary = summarise_study(results)
    return {"summary": summary, "events": results}
