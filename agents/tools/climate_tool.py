"""
Climate Data Tool - Fetches real climate/weather data from APIs
Uses real APIs: OpenWeatherMap, NOAA, etc.
"""
import requests
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
import os

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    class BaseTool:
        pass


def fetch_openweather_data(location: str, api_key: str = None) -> Dict[str, Any]:
    """
    Fetch real weather data from OpenWeatherMap API
    
    Args:
        location: City name or coordinates
        api_key: OpenWeatherMap API key (from env if not provided)
        
    Returns:
        Weather data dictionary
    """
    api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY not set in environment")
    
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching OpenWeather data: {e}")
        raise


def fetch_weather_forecast(location: str, days: int = 5, api_key: str = None) -> Dict[str, Any]:
    """
    Fetch weather forecast from OpenWeatherMap
    
    Args:
        location: City name
        days: Number of days to forecast (max 5 for free tier)
        api_key: API key
        
    Returns:
        Forecast data
    """
    api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError("OPENWEATHER_API_KEY not set")
    
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",
        "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching forecast: {e}")
        raise


def fetch_noaa_climate_data(station_id: str = None) -> Dict[str, Any]:
    """
    Fetch climate data from NOAA API (free, no key required)
    
    Args:
        station_id: Optional weather station ID
        
    Returns:
        Climate data
    """
    # NOAA API endpoint (example - may need adjustment)
    base_url = "https://www.ncei.noaa.gov/cdo/web/api/v2/data"
    
    # For demo, use a simple endpoint
    # Note: Full NOAA API requires registration but has free tier
    try:
        # Using a public NOAA endpoint
        url = "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/global/time-series/globe/land_ocean/1/1880-2024.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching NOAA data: {e}")
        # Return structure even if API fails
        return {
            "error": str(e),
            "note": "NOAA API may require registration"
        }


class ClimateDataTool(BaseTool):
    """Tool for fetching real climate/weather data"""
    
    name: str = "climate_data"
    description: str = "Fetch real climate and weather data from OpenWeatherMap and NOAA APIs. Use this for weather-related prediction markets (e.g., 'Will it rain tomorrow?')."
    parameters: dict = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Location (city name, e.g., 'London', 'New York')"
            },
            "data_type": {
                "type": "string",
                "description": "Type of data: 'current', 'forecast', 'climate'",
                "enum": ["current", "forecast", "climate"],
                "default": "current"
            },
            "days": {
                "type": "integer",
                "description": "Number of days for forecast (1-5)",
                "default": 1
            }
        },
        "required": ["location"]
    }
    
    async def execute(
        self,
        location: str,
        data_type: str = "current",
        days: int = 1
    ) -> str:
        """
        Execute climate data fetch
        
        Args:
            location: Location name
            data_type: Type of data to fetch
            days: Days for forecast
            
        Returns:
            JSON string with climate data
        """
        try:
            if data_type == "current":
                data = fetch_openweather_data(location)
                result = {
                    "location": location,
                    "temperature": data.get("main", {}).get("temp"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "pressure": data.get("main", {}).get("pressure"),
                    "weather": data.get("weather", [{}])[0].get("main"),
                    "description": data.get("weather", [{}])[0].get("description"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "timestamp": datetime.now().isoformat()
                }
            elif data_type == "forecast":
                data = fetch_weather_forecast(location, days)
                forecasts = []
                for item in data.get("list", [])[:days]:
                    forecasts.append({
                        "datetime": item.get("dt_txt"),
                        "temperature": item.get("main", {}).get("temp"),
                        "weather": item.get("weather", [{}])[0].get("main"),
                        "description": item.get("weather", [{}])[0].get("description"),
                        "precipitation": item.get("rain", {}).get("3h", 0) if "rain" in item else 0
                    })
                result = {
                    "location": location,
                    "forecasts": forecasts,
                    "days": days
                }
            else:  # climate
                data = fetch_noaa_climate_data()
                result = {
                    "location": location,
                    "climate_data": data,
                    "note": "NOAA climate data"
                }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "location": location,
                "data_type": data_type
            }, indent=2)

