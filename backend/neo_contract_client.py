"""
Neo Contract Interaction Client
Based on spoon-toolkit patterns - using neo-mamba library
Interacts with Neo contracts using RPC calls following reference implementation
"""
import asyncio
import json
import os
import ssl
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime

import aiohttp
from neo3.api import NeoRpcClient
from neo3.core import types
from neo3.wallet import utils as walletutils

# RPC URLs for different networks
DEFAULT_MAINNET_RPC = "https://mainmagnet.ngd.network:443"
DEFAULT_TESTNET_RPC = "https://testmagnet.ngd.network:443"


class NeoContractClient:
    """
    Client for interacting with Neo smart contracts via RPC
    Following spoon-toolkit reference implementation using neo-mamba
    """
    
    def __init__(self, rpc_url: str, contract_hash: str, network: str = "testnet"):
        """
        Initialize the Neo contract client
        
        Args:
            rpc_url: Neo RPC endpoint URL
            contract_hash: Contract hash (with or without 0x prefix)
            network: Network type ('mainnet' or 'testnet')
        """
        if network not in ["mainnet", "testnet"]:
            raise ValueError("Network must be 'mainnet' or 'testnet'")
        
        self.network = network
        self.rpc_url = rpc_url or (
            os.getenv("NEO_MAINNET_RPC", DEFAULT_MAINNET_RPC)
            if network == "mainnet"
            else os.getenv("NEO_TESTNET_RPC", DEFAULT_TESTNET_RPC)
        )
        
        # Initialize neo-mamba RPC client
        self.rpc_client = NeoRpcClient(self.rpc_url)
        
        # Store contract hash (normalize to remove 0x prefix for RPC calls)
        self.contract_hash = contract_hash
        self.contract_hash_clean = contract_hash.replace('0x', '') if contract_hash.startswith('0x') else contract_hash
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_timeout = float(os.getenv("NEO_RPC_TIMEOUT", "60"))
    
    def _normalize_address(self, raw: str) -> Tuple[str, types.UInt160]:
        """
        Normalize an address into Base58 address + script hash tuple.
        
        Args:
            raw: Address supplied by the caller, either Base58 or 0x-prefixed script hash.
            
        Returns:
            Tuple containing the Base58 encoded address and its script hash.
            
        Raises:
            ValueError: If the provided value cannot be parsed for the current network.
        """
        # Handle addresses passed in as 0x-prefixed script hashes.
        if raw.startswith("0x"):
            raw = raw[2:]
        
        try:
            script_hash = types.UInt160.from_string(raw)
            normalized_address = walletutils.script_hash_to_address(script_hash)
        except ValueError:
            # Fall back to validating/parsing the provided Base58 address.
            walletutils.validate_address(raw)
            normalized_address = raw
            script_hash = walletutils.address_to_script_hash(raw)
        
        return normalized_address, script_hash
    
    def _ensure_0x_prefix(self, value: str) -> str:
        """
        Ensure the value starts with 0x prefix. If not, add it.
        
        Args:
            value: The value to ensure has 0x prefix (e.g., hash, contract hash)
            
        Returns:
            str: The value with 0x prefix
        """
        if not value:
            return value
        if not value.startswith("0x"):
            return f"0x{value}"
        return value
    
    def _address_to_script_hash(self, address: str) -> str:
        """
        Convert an address to script hash format (0x...).
        
        This method handles both Base58 addresses and 0x-prefixed script hashes.
        If the address is already in script hash format, it returns it as-is.
        Otherwise, it converts the Base58 address to script hash format.
        
        Args:
            address: Neo address in Base58 format or script hash format (0x...)
            
        Returns:
            str: Address in script hash format (0x...)
        """
        if address.startswith("0x"):
            # Already in script hash format
            return address
        else:
            # Convert Base58 address to script hash format
            _, script_hash = self._normalize_address(address)
            return f"0x{str(script_hash).replace('0x', '')}"
    
    def _handle_response(self, result: Any) -> Any:
        """Handle neo-mamba response and extract result."""
        if result is None:
            raise RuntimeError("Empty response from Neo RPC")
        return result
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure an aiohttp client session exists for raw RPC calls."""
        if self._session and not self._session.closed:
            return self._session
        
        ssl_context = ssl.create_default_context()
        if os.getenv("NEO_RPC_ALLOW_INSECURE", "false").lower() in {"1", "true", "yes"}:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Increase connection timeout and total timeout for slow networks
        timeout = aiohttp.ClientTimeout(
            total=self._request_timeout,
            connect=30,  # Connection timeout (30 seconds)
            sock_read=self._request_timeout  # Socket read timeout
        )
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session
    
    async def _make_request(self, method: str, params) -> Any:
        """
        Send a JSON-RPC request to the configured Neo endpoint.
        
        Many higher-level toolkit functions call RPC extensions not yet exposed
        by neo-mamba. This helper issues the request directly; if the remote node
        does not recognise the method we return a descriptive string rather than
        raising so the caller can surface the limitation gracefully.
        """
        session = await self._ensure_session()
        
        rpc_method = method
        
        # Handle both dict and list params
        # Neo extended APIs use dict params, standard JSON-RPC uses list params
        if params is None:
            params_value = []
        elif isinstance(params, dict):
            params_value = params  # Keep dict as-is for extended APIs
        else:
            params_value = params  # Keep list as-is for standard APIs
        
        payload = {
            "jsonrpc": "2.0",
            "method": rpc_method,
            "params": params_value,
            "id": 1,
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self._request_timeout)
            async with session.post(self.rpc_url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except asyncio.TimeoutError as exc:
            return f"RPC request timeout for '{method}' (timeout: {self._request_timeout}s, URL: {self.rpc_url}): {exc}"
        except aiohttp.ClientError as exc:
            return f"RPC request failed for '{method}' (URL: {self.rpc_url}): {exc}"
        except Exception as exc:  # pragma: no cover - defensive
            return f"Unexpected RPC error for '{method}' (URL: {self.rpc_url}): {type(exc).__name__}: {exc}"
        
        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            if isinstance(error, dict):
                message = error.get("message", str(error))
                code = error.get("code", "unknown")
                return f"RPC method '{method}' returned error (code: {code}): {message}"
            else:
                return f"RPC method '{method}' returned error: {error}"
        
        return data.get("result") if isinstance(data, dict) else data
    
    def _convert_to_contract_param(self, value: Any, param_type: str) -> Dict[str, Any]:
        """Convert Python value to Neo contract parameter format"""
        if param_type == "String":
            return {"type": "String", "value": str(value)}
        elif param_type == "Integer":
            return {"type": "Integer", "value": int(value)}
        elif param_type == "Boolean":
            return {"type": "Boolean", "value": bool(value)}
        elif param_type == "ByteArray":
            if isinstance(value, str):
                # Convert hex string to byte array
                if value.startswith('0x'):
                    value = value[2:]
                return {"type": "ByteArray", "value": value}
            return {"type": "ByteArray", "value": value}
        elif param_type == "Hash160":
            # Convert address or hash to Hash160 format
            if isinstance(value, str):
                if value.startswith('0x'):
                    value = value[2:]
                return {"type": "Hash160", "value": value}
            return {"type": "Hash160", "value": value}
        else:
            return {"type": param_type, "value": value}
    
    async def invoke_read(
        self,
        operation: str,
        args: List[Tuple[Any, str]] = None,
        signers: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Invoke a read-only contract method
        
        Args:
            operation: Contract method name
            args: List of (value, type) tuples for arguments
            signers: Optional list of signers
            
        Returns:
            Dict containing the invocation result
        """
        # Convert args to contract parameter format
        contract_args = []
        if args:
            for arg_value, arg_type in args:
                contract_args.append(self._convert_to_contract_param(arg_value, arg_type))
        
        # Build invoke function parameters
        invoke_params = [
            self.contract_hash_clean,
            operation,
            contract_args
        ]
        
        if signers:
            invoke_params.append(signers)
        
        result = await self._make_request("invokefunction", invoke_params)
        
        # Check if result is an error string
        if isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower() or "timeout" in result.lower()):
            raise Exception(result)
        
        return self._handle_response(result)
    
    async def get_market(self, market_id: str) -> Optional[Dict[str, Any]]:
        """
        Get market data from contract
        Calls getMarket(string marketId) method
        """
        try:
            result = await self.invoke_read(
                "getMarket",
                args=[(market_id, "String")]
            )
            
            # Parse stack result
            if "stack" in result and len(result["stack"]) > 0:
                # The result is in the stack - parse it
                stack_item = result["stack"][0]
                
                # If it's a struct/array, we need to parse it
                if stack_item.get("type") == "Array":
                    # Parse array of market data
                    values = stack_item.get("value", [])
                    if len(values) >= 11:  # Based on MarketData structure
                        return {
                            "id": market_id,
                            "question": self._parse_stack_value(values[0]) if len(values) > 0 else "",
                            "description": self._parse_stack_value(values[1]) if len(values) > 1 else "",
                            "category": self._parse_stack_value(values[2]) if len(values) > 2 else "",
                            "resolve_date": self._parse_stack_value(values[3]) if len(values) > 3 else 0,
                            "oracle_url": self._parse_stack_value(values[4]) if len(values) > 4 else "",
                            "creator": self._parse_stack_value(values[5]) if len(values) > 5 else "",
                            "created_at": self._parse_stack_value(values[6]) if len(values) > 6 else 0,
                            "yes_shares": self._parse_stack_value(values[7]) if len(values) > 7 else 0,
                            "no_shares": self._parse_stack_value(values[8]) if len(values) > 8 else 0,
                            "resolved": self._parse_stack_value(values[9]) if len(values) > 9 else False,
                            "outcome": self._parse_stack_value(values[10]) if len(values) > 10 else False,
                        }
                elif stack_item.get("type") == "ByteString":
                    # Might be null/empty
                    return None
            
            return None
        except Exception as e:
            print(f"Error getting market: {e}")
            return None
    
    def _parse_stack_value(self, value: Any) -> Any:
        """Parse value from stack item"""
        if isinstance(value, dict):
            if "value" in value:
                return value["value"]
            return value
        return value
    
    async def get_market_count(self) -> int:
        """Get total number of markets"""
        try:
            result = await self.invoke_read("getMarketCount", args=[])
            if "stack" in result and len(result["stack"]) > 0:
                value = result["stack"][0].get("value", "0")
                return int(value) if isinstance(value, (int, str)) else 0
            return 0
        except Exception as e:
            print(f"Error getting market count: {e}")
            return 0
    
    async def get_probability(self, market_id: str) -> float:
        """
        Get probability for a market
        Returns probability as percentage (0-100)
        """
        try:
            result = await self.invoke_read(
                "getProbability",
                args=[(market_id, "String")]
            )
            if "stack" in result and len(result["stack"]) > 0:
                value = result["stack"][0].get("value", "5000")
                # Contract returns 0-10000 (where 10000 = 100%)
                prob_int = int(value) if isinstance(value, (int, str)) else 5000
                return prob_int / 100.0  # Convert to percentage
            return 50.0
        except Exception as e:
            print(f"Error getting probability: {e}")
            return 50.0
    
    async def get_user_shares(
        self,
        market_id: str,
        user_address: str,
        side: str = "yes"
    ) -> int:
        """
        Get user's shares for a market
        side: "yes" or "no"
        """
        try:
            method = "getUserYesShares" if side == "yes" else "getUserNoShares"
            # Convert address to script hash format
            address_script_hash = self._address_to_script_hash(user_address)
            # Remove 0x prefix for Hash160 parameter
            clean_address = address_script_hash.replace('0x', '')
            
            result = await self.invoke_read(
                method,
                args=[
                    (market_id, "String"),
                    (clean_address, "Hash160")
                ]
            )
            if "stack" in result and len(result["stack"]) > 0:
                value = result["stack"][0].get("value", "0")
                return int(value) if isinstance(value, (int, str)) else 0
            return 0
        except Exception as e:
            print(f"Error getting user shares: {e}")
            return 0
    
    async def prepare_create_market_tx(
        self,
        question: str,
        description: str,
        category: str,
        resolve_date: int,  # Unix timestamp
        oracle_url: str
    ) -> Dict[str, Any]:
        """
        Prepare createMarket transaction data
        Returns transaction data for frontend to sign
        """
        # Return transaction data structure for frontend
        return {
            "script_hash": self.contract_hash,
            "operation": "createMarket",
            "args": [
                {"type": "String", "value": question},
                {"type": "String", "value": description},
                {"type": "String", "value": category},
                {"type": "Integer", "value": resolve_date},
                {"type": "String", "value": oracle_url}
            ],
            "fee": "0.01"
        }
    
    async def prepare_trade_tx(
        self,
        market_id: str,
        side: str,  # "yes" or "no"
        amount: int  # Amount in smallest unit (e.g., satoshis for GAS)
    ) -> Dict[str, Any]:
        """
        Prepare trade transaction data
        Returns transaction data for frontend to sign
        """
        operation = "buyYes" if side == "yes" else "buyNo"
        
        return {
            "script_hash": self.contract_hash,
            "operation": operation,
            "args": [
                {"type": "String", "value": market_id},
                {"type": "Integer", "value": amount}
            ],
            "fee": "0.01"
        }
    
    async def prepare_resolve_request_tx(
        self,
        market_id: str,
        oracle_url: str,
        filter: str,
        callback_method: str = "onOracleCallback"
    ) -> Dict[str, Any]:
        """
        Prepare requestResolve transaction
        This will trigger Oracle request
        """
        return {
            "script_hash": self.contract_hash,
            "operation": "requestResolve",
            "args": [
                {"type": "String", "value": market_id},
                {"type": "String", "value": oracle_url},
                {"type": "String", "value": filter},
                {"type": "String", "value": callback_method}
            ],
            "fee": "0.01"
        }
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
