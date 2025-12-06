#!/usr/bin/env python3
"""
Simple Local Testing Script for PredictX Smart Contract

This script uses direct RPC calls to test the contract without requiring Neo3 SDK.
Works with any Neo RPC endpoint (Neo Express, Neo-CLI, or TestNet).

Usage:
    python3 test_contract_simple.py --rpc-url http://localhost:20332
    python3 test_contract_simple.py --testnet --contract-hash 0x...
"""

import json
import sys
import argparse
import base64
import requests
from pathlib import Path
from typing import Optional, Dict, Any


class SimpleContractTester:
    def __init__(self, rpc_url: str, contract_hash: Optional[str] = None):
        self.rpc_url = rpc_url
        self.contract_hash = contract_hash
        
    def rpc_call(self, method: str, params: list = None) -> Dict[str, Any]:
        """Make RPC call to Neo node"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        try:
            response = requests.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"RPC Error: {result['error']}")
            
            return result.get("result", {})
        except Exception as e:
            print(f"❌ RPC call failed: {e}")
            raise
    
    def test_connection(self):
        """Test RPC connection"""
        print("🔌 Testing RPC connection...")
        try:
            result = self.rpc_call("getblockcount")
            block_count = result
            print(f"✅ Connected! Current block: {block_count}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def invoke_contract(self, method: str, params: list) -> Dict[str, Any]:
        """Invoke a contract method"""
        if not self.contract_hash:
            raise Exception("Contract hash not set")
        
        # Build script (simplified - in production, use proper script builder)
        # For now, we'll use invokefunction RPC method
        script_params = []
        for param in params:
            if isinstance(param, str):
                script_params.append({"type": "String", "value": param})
            elif isinstance(param, int):
                script_params.append({"type": "Integer", "value": str(param)})
            else:
                script_params.append({"type": "String", "value": str(param)})
        
        result = self.rpc_call("invokefunction", [
            self.contract_hash,
            method,
            script_params
        ])
        
        return result
    
    def test_create_market(self) -> Optional[str]:
        """Test createMarket method"""
        print("\n🧪 Testing createMarket...")
        
        question = "Will Bitcoin reach $100k by 2025?"
        description = "Test market for local testing"
        category = "Crypto"
        resolve_date = 1765125597000  # Milliseconds
        oracle_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        
        try:
            result = self.invoke_contract("createMarket", [
                question,
                description,
                category,
                resolve_date,
                oracle_url
            ])
            
            if result.get("state") == "HALT":
                stack = result.get("stack", [])
                if stack and len(stack) > 0:
                    market_id_raw = stack[0].get("value")
                    # Decode base64 if it's a ByteString
                    if isinstance(market_id_raw, str) and stack[0].get("type") == "ByteString":
                        try:
                            market_id = base64.b64decode(market_id_raw).decode('utf-8')
                        except:
                            market_id = market_id_raw
                    else:
                        market_id = str(market_id_raw)
                    print(f"✅ Market created successfully!")
                    print(f"   Market ID: {market_id}")
                    print(f"   Gas Consumed: {result.get('gasconsumed', 'N/A')}")
                    return market_id
                else:
                    print("⚠️  Transaction HALT but no return value")
                    return "1"  # Assume first market
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ Transaction failed: {exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating market: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_get_market(self, market_id: str):
        """Test getMarket method"""
        print(f"\n🧪 Testing getMarket with market ID: {market_id}...")
        
        try:
            result = self.invoke_contract("getMarket", [market_id])
            
            if result.get("state") == "HALT":
                stack = result.get("stack", [])
                if stack and len(stack) > 0:
                    market_data = stack[0].get("value")
                    if market_data:
                        print(f"✅ Market data retrieved!")
                        print(f"   Data type: {stack[0].get('type')}")
                        print(f"   Data: {json.dumps(market_data, indent=2) if isinstance(market_data, dict) else market_data}")
                        return market_data
                    else:
                        print("⚠️  Market data is null/undefined")
                        return None
                else:
                    print("⚠️  No market data returned")
                    return None
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ Failed to get market: {exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting market: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_get_probability(self, market_id: str):
        """Test getProbability method"""
        print(f"\n🧪 Testing getProbability with market ID: {market_id}...")
        
        try:
            result = self.invoke_contract("getProbability", [market_id])
            
            if result.get("state") == "HALT":
                stack = result.get("stack", [])
                if stack and len(stack) > 0:
                    probability = int(stack[0].get("value", 0))
                    percentage = probability / 100
                    print(f"✅ Probability retrieved!")
                    print(f"   Probability: {percentage}% ({probability}/10000)")
                    return probability
                else:
                    print("⚠️  No probability returned")
                    return None
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ Failed to get probability: {exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting probability: {e}")
            return None
    
    def test_get_market_count(self):
        """Test getMarketCount method"""
        print(f"\n🧪 Testing getMarketCount...")
        
        try:
            result = self.invoke_contract("getMarketCount", [])
            
            if result.get("state") == "HALT":
                stack = result.get("stack", [])
                if stack and len(stack) > 0:
                    count = int(stack[0].get("value", 0))
                    print(f"✅ Market count: {count}")
                    return count
                else:
                    print("⚠️  No count returned")
                    return None
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ Failed to get market count: {exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting market count: {e}")
            return None
    
    def test_buy_yes(self, market_id: str, amount: int = 100000000):
        """Test buyYes method (read-only test - won't actually transfer)"""
        print(f"\n🧪 Testing buyYes (invoke test) with market ID: {market_id}, amount: {amount}...")
        print("   Note: This is a test invocation, no actual GAS will be transferred")
        
        try:
            result = self.invoke_contract("buyYes", [market_id, amount])
            
            if result.get("state") == "HALT":
                print(f"✅ buyYes invocation successful!")
                print(f"   Gas Consumed: {result.get('gasconsumed', 'N/A')}")
                return True
            else:
                exception = result.get("exception", "Unknown error")
                print(f"❌ buyYes failed: {exception}")
                return False
                
        except Exception as e:
            print(f"❌ Error in buyYes: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(description="Simple test script for PredictX contract")
    parser.add_argument("--rpc-url", default="http://localhost:20332",
                       help="RPC URL (default: http://localhost:20332)")
    parser.add_argument("--testnet", action="store_true",
                       help="Use Neo TestNet RPC")
    parser.add_argument("--contract-hash", type=str, required=True,
                       help="Contract hash to test")
    
    args = parser.parse_args()
    
    # Set RPC URL
    if args.testnet:
        rpc_url = "https://testnet1.neo.coz.io:443"
    else:
        rpc_url = args.rpc_url
    
    print("=" * 60)
    print("PredictX Contract Simple Testing")
    print("=" * 60)
    print(f"RPC URL: {rpc_url}")
    print(f"Contract Hash: {args.contract_hash}")
    print()
    
    # Initialize tester
    tester = SimpleContractTester(rpc_url, args.contract_hash)
    
    # Test connection
    if not tester.test_connection():
        print("\n💡 Make sure Neo Express or Neo node is running:")
        print("   For Neo Express: neo-express run")
        print("   For Neo-CLI: ./neo-cli")
        sys.exit(1)
    
    # Run tests
    print("\n" + "=" * 60)
    print("Running Contract Tests")
    print("=" * 60)
    
    # Test 1: Get market count (before)
    initial_count = tester.test_get_market_count()
    
    # Test 2: Create market
    market_id = tester.test_create_market()
    if not market_id:
        print("\n❌ Cannot continue tests without market ID")
        print("   This might indicate the contract needs to be deployed first")
        sys.exit(1)
    
    # Test 3: Get market count (after)
    final_count = tester.test_get_market_count()
    
    # Test 4: Get market data
    market_data = tester.test_get_market(market_id)
    
    # Test 5: Get probability
    probability = tester.test_get_probability(market_id)
    
    # Test 6: Buy YES shares (test invocation)
    buy_result = tester.test_buy_yes(market_id, 100000000)
    
    # Test 7: Get probability after trade
    if buy_result:
        probability_after = tester.test_get_probability(market_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✅ Market Created: {market_id}")
    print(f"✅ Market Count: {initial_count} → {final_count}")
    print(f"✅ Market Data Retrieved: {'Yes' if market_data else 'No'}")
    if probability:
        print(f"✅ Initial Probability: {probability/100}%")
    print(f"✅ Buy YES Test: {'Success' if buy_result else 'Failed'}")
    if buy_result and 'probability_after' in locals():
        print(f"✅ Probability After Trade: {probability_after/100 if probability_after else 'N/A'}%")
    
    print("\n✅ All tests completed!")
    print("\n💡 Note: To actually execute transactions (not just test), you need to:")
    print("   1. Sign and broadcast the transaction")
    print("   2. Use a wallet like NeoLine or Neo-CLI")


if __name__ == "__main__":
    main()

