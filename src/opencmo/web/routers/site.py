"""Public site metadata and lightweight analytics routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


@router.get("/site/stats")
async def api_v1_site_stats():
    return JSONResponse({
        "total_visits": await storage.get_site_counter("total_visits"),
        "unique_visitors": await storage.get_site_counter("unique_visitors"),
    })
