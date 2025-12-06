"""
Neo RPC Tool for interacting with Neo blockchain
"""
import requests
import json
from typing import Dict, Any
import os

try:
    from spoon_ai.tools.base import BaseTool
except ImportError:
    # Fallback for when spoon-ai-sdk is not installed
    class BaseTool:
        pass


def call_neo_rpc(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call Neo RPC endpoint
    
    Args:
        method: RPC method name (e.g., 'getblock', 'invokefunction')
        params: Parameters for the RPC call
        
    Returns:
        RPC response dictionary
    """
    rpc_url = os.getenv("NEO_RPC_URL", "http://localhost:20332")
    
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling Neo RPC: {e}")
        return {"error": str(e)}


class NeoRPCTool(BaseTool):
    """Tool wrapper for Neo RPC calls"""
    
    name: str = "neo_rpc_call"
    description: str = "Call Neo blockchain RPC methods to get market data, contract state, and transaction information."
    parameters: dict = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "description": "RPC method name (e.g., 'getblock', 'invokefunction', 'getapplicationlog')"
            },
            "params": {
                "type": "object",
                "description": "Parameters for the RPC call as a dictionary"
            }
        },
        "required": ["method"]
    }
    
    async def execute(self, method: str, params: Dict[str, Any] = None) -> str:
        """
        Execute Neo RPC call
        
        Args:
            method: RPC method name
            params: RPC parameters
            
        Returns:
            JSON string with RPC response
        """
        result = call_neo_rpc(method, params)
        return json.dumps(result, indent=2)

