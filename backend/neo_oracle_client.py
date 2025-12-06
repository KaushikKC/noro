"""
Neo Oracle Integration Client
Based on: https://developers.neo.org/docs/n3/Advances/Oracles

Oracle integration follows the contract-based pattern as per Neo documentation:
- Oracle requests are made through smart contract calls (Oracle.Request)
- Oracle callbacks are handled by contract methods with specific signature
- The contract must verify Oracle.Hash in callback

Key points from documentation:
1. Oracle.Request(url, filter, callback, userData, gasForResponse)
2. Callback signature: Callback(string url, byte[] userData, int code, byte[] result)
3. Minimum gasForResponse: 0.1 GAS (10000000 in smallest unit)
4. Default Oracle request fee: 0.5 GAS
5. Filter supports JSONPath expressions (max 128 bytes)
6. URL max length: 256 bytes
"""
import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

import aiohttp
from neo3.api import NeoRpcClient


class NeoOracleClient:
    """
    Client for interacting with Neo Oracle service
    Handles Oracle request preparation and response monitoring
    
    Note: Oracle requests are made through contract invocation.
    The contract must call Oracle.Request() method.
    """
    
    def __init__(self, rpc_url: str, oracle_hash: Optional[str] = None):
        """
        Initialize Neo Oracle client
        
        Args:
            rpc_url: Neo RPC endpoint
            oracle_hash: Oracle contract hash (optional, default is N3 Oracle hash)
        """
        self.rpc_url = rpc_url
        # Default Oracle contract hash on Neo N3
        self.oracle_hash = oracle_hash or "0xfe924b7cfe89ddd271abaf7210a80a7e11178758"
        self.rpc_client = NeoRpcClient(self.rpc_url)
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_timeout = float(os.getenv("NEO_RPC_TIMEOUT", "60"))
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure an aiohttp client session exists for raw RPC calls."""
        if self._session and not self._session.closed:
            return self._session
        
        import ssl
        ssl_context = ssl.create_default_context()
        if os.getenv("NEO_RPC_ALLOW_INSECURE", "false").lower() in {"1", "true", "yes"}:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        timeout = aiohttp.ClientTimeout(
            total=self._request_timeout,
            connect=30,
            sock_read=self._request_timeout
        )
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session
    
    async def _make_request(self, method: str, params) -> Any:
        """Send a JSON-RPC request to the configured Neo endpoint."""
        session = await self._ensure_session()
        
        if params is None:
            params_value = []
        elif isinstance(params, dict):
            params_value = params
        else:
            params_value = params
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params_value,
            "id": 1,
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=self._request_timeout)
            async with session.post(self.rpc_url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except asyncio.TimeoutError as exc:
            return f"RPC request timeout for '{method}': {exc}"
        except aiohttp.ClientError as exc:
            return f"RPC request failed for '{method}': {exc}"
        except Exception as exc:
            return f"Unexpected RPC error for '{method}': {type(exc).__name__}: {exc}"
        
        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            if isinstance(error, dict):
                message = error.get("message", str(error))
                code = error.get("code", "unknown")
                return f"RPC method '{method}' returned error (code: {code}): {message}"
            else:
                return f"RPC method '{method}' returned error: {error}"
        
        return data.get("result") if isinstance(data, dict) else data
    
    async def get_oracle_price(self) -> Optional[float]:
        """
        Get current Oracle service price (in GAS)
        
        According to documentation, default fee is 0.5 GAS per request
        """
        try:
            result = await self._make_request("invokefunction", [
                self.oracle_hash.replace('0x', ''),
                "getPrice",
                []
            ])
            
            if isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower()):
                print(f"Error getting Oracle price: {result}")
                return 0.5  # Default fee
            
            if isinstance(result, dict) and "stack" in result and len(result["stack"]) > 0:
                value = result["stack"][0].get("value", "50000000")  # 0.5 GAS default
                # Price is in smallest unit, divide by 10^8
                return int(value) / 100000000 if isinstance(value, (int, str)) else 0.5
            return 0.5  # Default fee
        except Exception as e:
            print(f"Error getting Oracle price: {e}")
            return 0.5  # Default fee
    
    async def prepare_market_resolution_request(
        self,
        contract_hash: str,
        market_id: str,
        oracle_url: str,
        filter: str = "$.outcome",
        gas_for_response: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Prepare Oracle request transaction for market resolution
        
        According to Neo Oracle documentation:
        - Oracle.Request(url, filter, callback, userData, gasForResponse)
        - url: max 256 bytes, must return JSON with Content-Type: application/json
        - filter: JSONPath expression, max 128 bytes
        - callback: method name in contract (cannot begin with "_"), max 32 bytes
        - userData: byte array (we pass marketId as bytes)
        - gasForResponse: minimum 0.1 GAS (10000000), fee for callback execution
        
        Args:
            contract_hash: noro contract hash
            market_id: Market ID to resolve (will be passed as userData)
            oracle_url: URL to fetch resolution data from (must return JSON)
            filter: JSONPath filter (default: "$.outcome" to extract outcome field)
            gas_for_response: GAS amount for callback (default: 0.1 GAS minimum)
            
        Returns:
            Transaction data structure for frontend to sign
        """
        # Minimum gasForResponse is 0.1 GAS (10000000 in smallest unit)
        if gas_for_response is None or gas_for_response < 10000000:
            gas_for_response = 10000000  # 0.1 GAS
        
        # Validate URL length (max 256 bytes)
        if len(oracle_url.encode('utf-8')) > 256:
            raise ValueError(f"Oracle URL too long: {len(oracle_url.encode('utf-8'))} bytes (max 256)")
        
        # Validate filter length (max 128 bytes)
        if len(filter.encode('utf-8')) > 128:
            raise ValueError(f"Filter too long: {len(filter.encode('utf-8'))} bytes (max 128)")
        
        # The contract method is requestResolve which calls Oracle.Request internally
        # Contract signature: RequestResolve(string marketId, string oracleUrl, string filter, long gasForResponse)
        return {
            "script_hash": contract_hash,
            "operation": "requestResolve",
            "args": [
                {"type": "String", "value": market_id},
                {"type": "String", "value": oracle_url},
                {"type": "String", "value": filter},
                {"type": "Integer", "value": gas_for_response}
            ],
            "fee": "0.55",  # 0.5 GAS for Oracle request + 0.05 GAS buffer
            "note": "Oracle request fee: 0.5 GAS + callback gas will be charged"
        }
    
    async def get_oracle_response(
        self,
        request_tx_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get Oracle response for a request
        
        Note: Oracle responses are handled automatically by the contract callback.
        This method can be used to monitor request status and view response data.
        
        Args:
            request_tx_hash: Transaction hash of the Oracle request
            
        Returns:
            Dict containing response information if available
        """
        try:
            # Get application log for the request transaction
            result = await self._make_request("getapplicationlog", [request_tx_hash])
            
            if isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower()):
                return None
            
            if isinstance(result, dict) and "executions" in result:
                executions = result["executions"]
                if len(executions) > 0:
                    execution = executions[0]
                    
                    # Look for Oracle-related notifications
                    if "notifications" in execution:
                        for notification in execution["notifications"]:
                            contract = notification.get("contract", "")
                            # Check if this is from Oracle contract or our contract
                            if contract.lower() == self.oracle_hash.replace('0x', '').lower():
                                return {
                                    "request_tx": request_tx_hash,
                                    "oracle_notification": notification,
                                    "type": "oracle_response"
                                }
                            # Check for market resolved event
                            state = notification.get("state", {})
                            if isinstance(state, dict):
                                value = state.get("value", [])
                                if isinstance(value, list) and len(value) > 0:
                                    # Check if this is MarketResolved event
                                    event_name = value[0] if len(value) > 0 else ""
                                    if "MarketResolved" in str(event_name):
                                        return {
                                            "request_tx": request_tx_hash,
                                            "market_resolved": True,
                                            "notification": notification
                                        }
            
            return None
        except Exception as e:
            print(f"Error getting Oracle response: {e}")
            return None
    
    def parse_oracle_result(self, result_bytes: bytes) -> Dict[str, Any]:
        """
        Parse Oracle callback result bytes
        
        According to documentation, Oracle returns filtered JSON data.
        The result is passed as byte[] to the callback function.
        
        Args:
            result_bytes: Result bytes from Oracle callback
            
        Returns:
            Parsed result dictionary
        """
        try:
            # Convert bytes to string
            result_string = result_bytes.decode('utf-8') if isinstance(result_bytes, bytes) else str(result_bytes)
            
            # Try to parse as JSON
            try:
                parsed = json.loads(result_string)
                return {
                    "success": True,
                    "data": parsed,
                    "raw": result_string
                }
            except json.JSONDecodeError:
                # If not JSON, try to extract outcome from string
                result_lower = result_string.lower()
                if "yes" in result_lower or "true" in result_lower or "1" in result_lower:
                    return {
                        "success": True,
                        "outcome": "YES",
                        "resolved": True,
                        "raw": result_string
                    }
                elif "no" in result_lower or "false" in result_lower or "0" in result_lower:
                    return {
                        "success": True,
                        "outcome": "NO",
                        "resolved": True,
                        "raw": result_string
                    }
                else:
                    return {
                        "success": False,
                        "outcome": None,
                        "resolved": False,
                        "raw": result_string,
                        "error": "Could not parse Oracle result"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "raw": str(result_bytes)
            }
    
    def validate_oracle_url(self, url: str) -> Dict[str, bool]:
        """
        Validate Oracle URL according to documentation
        
        Supported schemes: https, neofs
        - https: Must return JSON with Content-Type: application/json
        - neofs: neofs://<Container-ID>/<Object-ID>[/<Command>/<Params>]
        
        Args:
            url: URL to validate
            
        Returns:
            Dict with validation result
        """
        if not url:
            return {"valid": False, "error": "URL is empty"}
        
        if len(url.encode('utf-8')) > 256:
            return {"valid": False, "error": f"URL too long: {len(url.encode('utf-8'))} bytes (max 256)"}
        
        if url.startswith("https://"):
            return {"valid": True, "scheme": "https", "note": "Must return JSON with Content-Type: application/json"}
        elif url.startswith("neofs://"):
            return {"valid": True, "scheme": "neofs", "note": "NeoFS URL format: neofs://<Container-ID>/<Object-ID>[/<Command>/<Params>]"}
        else:
            return {"valid": False, "error": "URL must start with https:// or neofs://"}
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()


class OracleWebhookHandler:
    """
    Handler for Oracle callback processing
    
    Note: In practice, Oracle callbacks are handled directly by the contract.
    This handler is for monitoring and processing Oracle responses.
    """
    
    def __init__(self, contract_client, oracle_client):
        """
        Initialize webhook handler
        
        Args:
            contract_client: NeoContractClient instance
            oracle_client: NeoOracleClient instance
        """
        self.contract_client = contract_client
        self.oracle_client = oracle_client
    
    async def handle_oracle_callback(
        self,
        url: str,
        user_data: bytes,
        code: int,
        result: bytes
    ) -> Dict[str, Any]:
        """
        Process Oracle callback data
        
        This simulates what the contract callback does.
        In practice, the contract handles this automatically.
        
        Args:
            url: Original Oracle request URL
            user_data: User data (marketId as bytes)
            code: Response code (0 = success)
            result: Result bytes from Oracle
            
        Returns:
            Processed result
        """
        # Check if request was successful
        if code != 0:
            return {
                "success": False,
                "error": f"Oracle request failed with code: {code}",
                "code": code
            }
        
        # Extract marketId from userData
        try:
            market_id = user_data.decode('utf-8') if isinstance(user_data, bytes) else str(user_data)
        except:
            market_id = str(user_data)
        
        # Parse Oracle result
        parsed_result = self.oracle_client.parse_oracle_result(result)
        
        if parsed_result.get("success"):
            outcome = parsed_result.get("outcome")
            if outcome:
                outcome_bool = outcome.upper() == "YES"
                return {
                    "success": True,
                    "market_id": market_id,
                    "resolved": True,
                    "outcome": outcome_bool,
                    "parsed_result": parsed_result
                }
        
        return {
            "success": False,
            "market_id": market_id,
            "resolved": False,
            "error": "Could not parse Oracle result",
            "parsed_result": parsed_result
        }
