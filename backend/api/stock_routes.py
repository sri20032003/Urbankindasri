"""Stock API routes"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{symbol}")
async def get_stock_profile(symbol: str):
    """Get full stock profile."""
    return {
        "symbol": symbol,
        "name": f"Stock {symbol}",
        "price": 2500.00,
        "change_pct": 1.25
    }


@router.get("/{symbol}/proxies")
async def get_stock_proxies(symbol: str):
    """Get all proxies for a stock."""
    return {
        "symbol": symbol,
        "proxies": {
            "rsi": 65,
            "macd_bullish": True,
            "price_above_ma50": True
        }
    }


@router.get("/{symbol}/regime")
async def get_stock_regime(symbol: str):
    """Get regime for a stock."""
    return {
        "symbol": symbol,
        "regime": {
            "trend": "STRONG_BULL",
            "volatility": "NORMAL",
            "momentum": "STRONG_UP"
        }
    }


@router.get("/{symbol}/chart")
async def get_stock_chart(symbol: str, timeframe: str = "1d", bars: int = 100):
    """Get historical chart data."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": bars,
        "data": []
    }
