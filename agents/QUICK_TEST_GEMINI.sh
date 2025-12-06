#!/bin/bash

# Quick test with Gemini API

echo "🧪 Testing noro Agents with Gemini"
echo "======================================="
echo ""

cd "$(dirname "$0")"
source venv/bin/activate

echo "1️⃣  Checking environment..."
python3 << 'PYTHON_SCRIPT'
import os
from dotenv import load_dotenv
load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")
provider = os.getenv("DEFAULT_LLM_PROVIDER", "not set")
model = os.getenv("DEFAULT_MODEL", "not set")

if gemini_key and gemini_key != "your_gemini_key_here":
    print(f"   ✅ GEMINI_API_KEY: SET")
else:
    print(f"   ❌ GEMINI_API_KEY: NOT SET")
    exit(1)

print(f"   ✅ DEFAULT_LLM_PROVIDER: {provider}")
print(f"   ✅ DEFAULT_MODEL: {model}")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Please set GEMINI_API_KEY in .env file"
    exit 1
fi

echo ""
echo "2️⃣  Testing Analyzer Agent with Gemini..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from analyzer_agent import AnalyzerAgent

async def test():
    print("   Testing weather market...")
    agent = AnalyzerAgent()  # Uses Gemini from .env
    result = await agent.analyze('Will it rain tomorrow in London?')
    
    print(f"   ✅ Probability: {result.get('probability', 0):.2%}")
    print(f"   ✅ Confidence: {result.get('confidence', 0):.2%}")
    print(f"   ✅ Sources: {result.get('sources_count', 0)}")
    
    if "Fallback" in result.get('evidence', ''):
        print("   ⚠️  Still using fallback - check API key")
    else:
        print("   ✅ Using REAL APIs!")

asyncio.run(test())
PYTHON_SCRIPT

echo ""
echo "3️⃣  Testing Full Orchestrator (All 3 Agents)..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from orchestrator import NoroOrchestrator

async def test():
    print("   Testing: Will it rain tomorrow in London?")
    orchestrator = NoroOrchestrator()  # Uses Gemini from .env
    
    result = await orchestrator.process_market(
        market_question='Will it rain tomorrow in London?',
        bankroll=1000.0
    )
    
    judgment = result.get('judgment', {})
    trade = result.get('trade_proposal', {})
    first_analysis = result.get('analyses', [{}])[0]
    
    print(f"   ✅ Consensus Probability: {judgment.get('consensus_probability', 0):.2%}")
    print(f"   ✅ Consensus Confidence: {judgment.get('consensus_confidence', 0):.2%}")
    print(f"   ✅ Agreement Level: {judgment.get('agreement_level', 'N/A')}")
    print(f"   ✅ Trade Action: {trade.get('action', 'N/A')}")
    print(f"   ✅ Trade Amount: {trade.get('amount', 0):.2f} GAS")
    print(f"   ✅ Sources Count: {first_analysis.get('sources_count', 0)}")
    
    if "Fallback" in first_analysis.get('evidence', ''):
        print("   ⚠️  Still using fallback - check API key")
    else:
        print("   ✅ All agents using REAL APIs with Gemini!")

asyncio.run(test())
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "✅ Test Complete!"
echo ""
echo "If you see 'Fallback' messages, check:"
echo "  1. GEMINI_API_KEY is set correctly in .env"
echo "  2. API key is valid"
echo "  3. You have internet connection"
echo ""

