"""Dashboard API routes"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/scanner")
async def get_scanner():
    """Live scanner endpoint."""
    return {
        "status": "ok",
        "stocks": []
    }


@router.get("/performance")
async def get_performance():
    """System performance metrics."""
    return {
        "accuracy": 0.68,
        "win_rate": 0.62,
        "avg_rr": 2.1,
        "total_signals": 150
    }


@router.get("/strategy/combinations")
async def get_strategy_combinations():
    """Get all strategy combinations."""
    return {
        "combinations": [
            "ema_adx_vwap",
            "rsi_macd_volume",
            "breakout_rs_volume"
        ]
    }
