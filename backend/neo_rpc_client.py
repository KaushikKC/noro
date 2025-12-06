"""
Neo RPC Client for interacting with Neo blockchain
"""
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class NeoRPCClient:
    """Client for Neo blockchain RPC calls"""
    
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
    
    async def _call_rpc(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """Make RPC call to Neo node"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"RPC Error: {result['error']}")
            
            return result.get("result", {})
        except Exception as e:
            print(f"RPC Error: {e}")
            raise
    
    async def get_block_count(self) -> int:
        """Get current block count"""
        result = await self._call_rpc("getblockcount")
        return result
    
    async def get_market(self, contract_hash: str, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get market data from contract storage
        Note: This is a simplified version - actual implementation depends on contract storage structure
        """
        try:
            # Call contract method to get market data
            # This is a placeholder - actual implementation depends on your contract methods
            result = await self._call_rpc("invokefunction", [
                contract_hash,
                "getMarket",
                [{"type": "String", "value": market_id}]
            ])
            
            # Parse result (structure depends on contract)
            # For now, return mock structure
            return {
                "id": market_id,
                "question": "Sample question",
                "description": "Sample description",
                "category": "Biology",
                "resolve_date": "2025-12-31",
                "creator": "0x0000000000000000000000000000000000000000",
                "created_at": datetime.now().isoformat(),
                "yes_shares": 1000.0,
                "no_shares": 500.0,
                "is_resolved": False,
                "outcome": None
            }
        except:
            return None
    
    async def get_all_markets(self, contract_hash: str) -> List[Dict[str, Any]]:
        """Get all markets from contract"""
        try:
            # Call contract method to get market count
            count_result = await self._call_rpc("invokefunction", [
                contract_hash,
                "getMarketCount",
                []
            ])
            
            # For now, return empty list or mock data
            # Actual implementation would iterate through markets
            return []
        except:
            return []
    
    async def prepare_create_market(
        self,
        contract_hash: str,
        question: str,
        description: str,
        category: str,
        resolve_date: str,
        oracle_url: str,
        initial_liquidity: float
    ) -> Dict[str, Any]:
        """
        Prepare create market transaction
        Returns transaction data for frontend to sign
        """
        # This would prepare the actual transaction
        # For now, return structure that frontend expects
        return {
            "script_hash": contract_hash,
            "operation": "createMarket",
            "args": [
                {"type": "String", "value": question},
                {"type": "String", "value": description},
                {"type": "String", "value": category},
                {"type": "String", "value": resolve_date},
                {"type": "String", "value": oracle_url},
                {"type": "Integer", "value": int(initial_liquidity * 100000000)}  # Convert to smallest unit
            ],
            "fee": "0.01"
        }
    
    async def prepare_trade(
        self,
        contract_hash: str,
        market_id: str,
        action: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Prepare trade transaction
        Returns transaction data for frontend to sign
        """
        # Convert action to contract parameter
        buy_yes = action == "BUY_YES"
        
        return {
            "script_hash": contract_hash,
            "operation": "trade",
            "args": [
                {"type": "String", "value": market_id},
                {"type": "Boolean", "value": buy_yes},
                {"type": "Integer", "value": int(amount * 100000000)}  # Convert to smallest unit
            ],
            "fee": "0.01"
        }

