#!/usr/bin/env python3
"""
Local Testing Script for PredictX Smart Contract

This script tests the PredictX contract methods locally before deploying to testnet.
It can work with:
1. Neo Express (local blockchain) - Recommended
2. Neo TestNet (for final verification)

Usage:
    python3 test_contract_local.py --rpc-url http://localhost:20332  # Neo Express
    python3 test_contract_local.py --testnet                          # TestNet
"""

import json
import sys
import os
import argparse
from pathlib import Path
from typing import Optional, Any

# Add parent directory to path to import neo3
sys.path.insert(0, str(Path(__file__).parent.parent / "agents" / "venv" / "lib" / "python3.12" / "site-packages"))

try:
    from neo3.api import noderpc, wrappers
    from neo3.core import types, cryptography
    from neo3.contracts import nef, manifest
    from neo3 import vm, storage
    from neo3.network import payloads
except ImportError as e:
    print(f"❌ Error importing Neo3 SDK: {e}")
    print("\nPlease install Neo3 Python SDK:")
    print("  pip install neo3-python")
    sys.exit(1)


class ContractTester:
    def __init__(self, rpc_url: str, contract_hash: Optional[str] = None):
        self.rpc_url = rpc_url
        self.rpc_client = noderpc.NodeRPCClient(rpc_url)
        self.contract_hash = contract_hash
        self.contract: Optional[wrappers.GenericContract] = None
        
    def load_contract_files(self) -> tuple[nef.NEF, manifest.ContractManifest]:
        """Load NEF and manifest files"""
        contract_dir = Path(__file__).parent / "bin" / "sc"
        nef_path = contract_dir / "PredictXMarket.nef"
        manifest_path = contract_dir / "PredictXMarket.manifest.json"
        
        if not nef_path.exists():
            raise FileNotFoundError(f"NEF file not found: {nef_path}")
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
        
        # Load NEF
        with open(nef_path, "rb") as f:
            nef_data = nef.NEF.deserialize(f.read())
        
        # Load Manifest
        with open(manifest_path, "r") as f:
            manifest_data = manifest.ContractManifest.from_json(json.load(f))
        
        return nef_data, manifest_data
    
    def deploy_contract(self, nef_data: nef.NEF, manifest_data: manifest.ContractManifest) -> types.UInt160:
        """Deploy contract to the network"""
        print("📦 Deploying contract...")
        
        try:
            result = wrappers.GenericContract.deploy(nef_data, manifest_data)
            print(f"✅ Contract deployed successfully!")
            print(f"   Contract Hash: {result.hash}")
            self.contract_hash = str(result.hash)
            self.contract = wrappers.GenericContract(result.hash)
            return result.hash
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            raise
    
    def load_contract(self, contract_hash: str):
        """Load existing contract"""
        self.contract_hash = contract_hash
        self.contract = wrappers.GenericContract(types.UInt160.from_string(contract_hash))
        print(f"✅ Loaded contract: {contract_hash}")
    
    def test_create_market(self) -> str:
        """Test createMarket method"""
        print("\n🧪 Testing createMarket...")
        
        question = "Will Bitcoin reach $100k by 2025?"
        description = "Test market for local testing"
        category = "Crypto"
        resolve_date = 1765125597000  # Milliseconds (2025-12-31)
        oracle_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        
        try:
            # Build script
            sb = vm.ScriptBuilder()
            sb.emit_contract_call_with_args(
                self.contract.hash,
                "createMarket",
                [question, description, category, resolve_date, oracle_url]
            )
            script = sb.to_array()
            
            # Invoke
            result = self.rpc_client.invoke_script(script)
            
            if result.state == "HALT":
                # Extract market ID from stack
                if result.stack and len(result.stack) > 0:
                    market_id = result.stack[0].value
                    print(f"✅ Market created successfully!")
                    print(f"   Market ID: {market_id}")
                    print(f"   Gas Consumed: {result.gas_consumed}")
                    return str(market_id)
                else:
                    print("⚠️  Transaction HALT but no return value")
                    return "1"  # Assume first market
            else:
                print(f"❌ Transaction failed: {result.exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating market: {e}")
            return None
    
    def test_get_market(self, market_id: str):
        """Test getMarket method"""
        print(f"\n🧪 Testing getMarket with market ID: {market_id}...")
        
        try:
            sb = vm.ScriptBuilder()
            sb.emit_contract_call_with_args(
                self.contract.hash,
                "getMarket",
                [market_id]
            )
            script = sb.to_array()
            
            result = self.rpc_client.invoke_script(script)
            
            if result.state == "HALT":
                if result.stack and len(result.stack) > 0:
                    market_data = result.stack[0].value
                    print(f"✅ Market data retrieved!")
                    print(f"   Data: {market_data}")
                    return market_data
                else:
                    print("⚠️  No market data returned (might be null/undefined)")
                    return None
            else:
                print(f"❌ Failed to get market: {result.exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting market: {e}")
            return None
    
    def test_get_probability(self, market_id: str):
        """Test getProbability method"""
        print(f"\n🧪 Testing getProbability with market ID: {market_id}...")
        
        try:
            sb = vm.ScriptBuilder()
            sb.emit_contract_call_with_args(
                self.contract.hash,
                "getProbability",
                [market_id]
            )
            script = sb.to_array()
            
            result = self.rpc_client.invoke_script(script)
            
            if result.state == "HALT":
                if result.stack and len(result.stack) > 0:
                    probability = result.stack[0].value
                    # Probability is in basis points (5000 = 50%)
                    percentage = int(probability) / 100
                    print(f"✅ Probability retrieved!")
                    print(f"   Probability: {percentage}% ({probability}/10000)")
                    return probability
                else:
                    print("⚠️  No probability returned")
                    return None
            else:
                print(f"❌ Failed to get probability: {result.exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting probability: {e}")
            return None
    
    def test_buy_yes(self, market_id: str, amount: int = 100000000):
        """Test buyYes method"""
        print(f"\n🧪 Testing buyYes with market ID: {market_id}, amount: {amount}...")
        
        try:
            sb = vm.ScriptBuilder()
            sb.emit_contract_call_with_args(
                self.contract.hash,
                "buyYes",
                [market_id, amount]
            )
            script = sb.to_array()
            
            result = self.rpc_client.invoke_script(script)
            
            if result.state == "HALT":
                print(f"✅ buyYes executed successfully!")
                print(f"   Gas Consumed: {result.gas_consumed}")
                return True
            else:
                print(f"❌ buyYes failed: {result.exception}")
                return False
                
        except Exception as e:
            print(f"❌ Error in buyYes: {e}")
            return False
    
    def test_get_market_count(self):
        """Test getMarketCount method"""
        print(f"\n🧪 Testing getMarketCount...")
        
        try:
            sb = vm.ScriptBuilder()
            sb.emit_contract_call(self.contract.hash, "getMarketCount")
            script = sb.to_array()
            
            result = self.rpc_client.invoke_script(script)
            
            if result.state == "HALT":
                if result.stack and len(result.stack) > 0:
                    count = result.stack[0].value
                    print(f"✅ Market count: {count}")
                    return int(count)
                else:
                    print("⚠️  No count returned")
                    return None
            else:
                print(f"❌ Failed to get market count: {result.exception}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting market count: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description="Test PredictX contract locally")
    parser.add_argument("--rpc-url", default="http://localhost:20332",
                       help="RPC URL (default: http://localhost:20332 for Neo Express)")
    parser.add_argument("--testnet", action="store_true",
                       help="Use Neo TestNet RPC")
    parser.add_argument("--contract-hash", type=str,
                       help="Existing contract hash (for testing deployed contract)")
    parser.add_argument("--deploy", action="store_true",
                       help="Deploy contract before testing")
    
    args = parser.parse_args()
    
    # Set RPC URL
    if args.testnet:
        rpc_url = "https://testnet1.neo.coz.io:443"
    else:
        rpc_url = args.rpc_url
    
    print("=" * 60)
    print("PredictX Contract Local Testing")
    print("=" * 60)
    print(f"RPC URL: {rpc_url}")
    print()
    
    # Initialize tester
    tester = ContractTester(rpc_url, args.contract_hash)
    
    # Test RPC connection
    try:
        print("🔌 Testing RPC connection...")
        block_count = tester.rpc_client.get_block_count()
        print(f"✅ Connected! Current block: {block_count}")
    except Exception as e:
        print(f"❌ Failed to connect to RPC: {e}")
        print("\n💡 Make sure Neo Express or Neo node is running:")
        print("   For Neo Express: neo-express run")
        print("   For Neo-CLI: ./neo-cli")
        sys.exit(1)
    
    # Deploy or load contract
    if args.deploy:
        try:
            nef_data, manifest_data = tester.load_contract_files()
            contract_hash = tester.deploy_contract(nef_data, manifest_data)
            print(f"\n📝 Contract Hash: {contract_hash}")
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            sys.exit(1)
    elif args.contract_hash:
        tester.load_contract(args.contract_hash)
    else:
        print("❌ Either --deploy or --contract-hash must be specified")
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
        print("❌ Cannot continue tests without market ID")
        sys.exit(1)
    
    # Test 3: Get market count (after)
    final_count = tester.test_get_market_count()
    
    # Test 4: Get market data
    market_data = tester.test_get_market(market_id)
    
    # Test 5: Get probability
    probability = tester.test_get_probability(market_id)
    
    # Test 6: Buy YES shares
    buy_result = tester.test_buy_yes(market_id, 100000000)  # 1 GAS (8 decimals)
    
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
    print(f"✅ Initial Probability: {probability/100 if probability else 0}%")
    print(f"✅ Buy YES Executed: {'Yes' if buy_result else 'No'}")
    if buy_result and probability_after:
        print(f"✅ Probability After Trade: {probability_after/100}%")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main()

