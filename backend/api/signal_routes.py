"""Signal API routes"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/active")
async def get_active_signals():
    """Get all active signals."""
    return {
        "status": "ok",
        "signals": []
    }


@router.get("/{symbol}")
async def get_signal_for_stock(symbol: str):
    """Get signal for a specific stock."""
    return {
        "symbol": symbol,
        "signal": "BUY",
        "quality": 85,
        "confidence": 0.82
    }


@router.post("/{symbol}/refresh")
async def refresh_signal(symbol: str, background_tasks: BackgroundTasks):
    """Force signal recalculation."""
    return {
        "status": "refreshing",
        "symbol": symbol
    }


@router.get("/history")
async def get_signal_history(stock: str, limit: int = 50):
    """Get signal history for a stock."""
    return {
        "symbol": stock,
        "history": []
    }
