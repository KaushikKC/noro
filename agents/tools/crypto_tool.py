"""
Crypto Data Tool - Fetches real cryptocurrency data from APIs
Uses real APIs: CoinGecko (free, no key required)
"""
import requests
import json
from typing import Dict, Any
from datetime import datetime

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    class BaseTool:
        pass


def fetch_coingecko_price(symbol: str, vs_currency: str = "usd") -> Dict[str, Any]:
    """
    Fetch real cryptocurrency price from CoinGecko API (free, no key)
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'bitcoin', 'ethereum')
        vs_currency: Currency to compare against (default: 'usd')
        
    Returns:
        Price data dictionary
    """
    base_url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol.lower(),
        "vs_currencies": vs_currency,
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if symbol.lower() not in data:
            raise ValueError(f"Symbol {symbol} not found")
        
        return data[symbol.lower()]
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        raise


def fetch_crypto_history(symbol: str, days: int = 7) -> Dict[str, Any]:
    """
    Fetch cryptocurrency historical data
    
    Args:
        symbol: Cryptocurrency symbol
        days: Number of days of history
        
    Returns:
        Historical price data
    """
    base_url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching crypto history: {e}")
        raise


class CryptoTool(BaseTool):
    """Tool for fetching real cryptocurrency data"""
    
    name: str = "crypto_data"
    description: str = "Fetch real cryptocurrency prices and data from CoinGecko API. Use this for crypto-related prediction markets (e.g., 'Will Bitcoin go up?')."
    parameters: dict = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Cryptocurrency symbol (e.g., 'bitcoin', 'ethereum', 'neo')"
            },
            "data_type": {
                "type": "string",
                "description": "Type of data: 'price', 'history'",
                "enum": ["price", "history"],
                "default": "price"
            },
            "days": {
                "type": "integer",
                "description": "Number of days for history (1-365)",
                "default": 7
            }
        },
        "required": ["symbol"]
    }
    
    async def execute(
        self,
        symbol: str,
        data_type: str = "price",
        days: int = 7
    ) -> str:
        """
        Execute crypto data fetch
        
        Args:
            symbol: Cryptocurrency symbol
            data_type: Type of data
            days: Days for history
            
        Returns:
            JSON string with crypto data
        """
        try:
            if data_type == "price":
                data = fetch_coingecko_price(symbol)
                result = {
                    "symbol": symbol.upper(),
                    "price_usd": data.get("usd"),
                    "change_24h": data.get("usd_24h_change"),
                    "volume_24h": data.get("usd_24h_vol"),
                    "market_cap": data.get("usd_market_cap"),
                    "timestamp": datetime.now().isoformat()
                }
            else:  # history
                data = fetch_crypto_history(symbol, days)
                prices = data.get("prices", [])
                result = {
                    "symbol": symbol.upper(),
                    "history_days": days,
                    "current_price": prices[-1][1] if prices else None,
                    "price_change": (prices[-1][1] - prices[0][1]) if len(prices) > 1 else 0,
                    "price_change_pct": ((prices[-1][1] - prices[0][1]) / prices[0][1] * 100) if len(prices) > 1 and prices[0][1] > 0 else 0,
                    "data_points": len(prices)
                }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "symbol": symbol,
                "data_type": data_type
            }, indent=2)

