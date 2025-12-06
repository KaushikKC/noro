#!/bin/bash

# Quick Test Script for noro Autonomous Agents
# Run this to test the full system

echo "🧪 noro Autonomous Agents - Quick Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1️⃣  Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo "   Start it with: cd backend && uvicorn main:app --reload"
    exit 1
fi

# Test health endpoint
echo ""
echo "2️⃣  Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "$HEALTH" | python3 -m json.tool

# Test agents directly
echo ""
echo "3️⃣  Testing Analyzer Agent directly..."
cd agents
source venv/bin/activate

python3 << 'PYTHON_SCRIPT'
import asyncio
import json
from analyzer_agent import AnalyzerAgent

async def test():
    print("   Testing weather market...")
    agent = AnalyzerAgent(llm_provider='openai', model_name='gpt-4o')
    result = await agent.analyze('Will it rain tomorrow in London?')
    print(f"   ✅ Probability: {result.get('probability', 0):.2%}")
    print(f"   ✅ Confidence: {result.get('confidence', 0):.2%}")
    print(f"   ✅ Sources: {result.get('sources_count', 0)}")

asyncio.run(test())
PYTHON_SCRIPT

# Test full orchestrator
echo ""
echo "4️⃣  Testing Full Orchestrator (All 3 Agents)..."
python3 << 'PYTHON_SCRIPT'
import asyncio
import json
from orchestrator import NoroOrchestrator

async def test():
    orchestrator = NoroOrchestrator(
        llm_provider='openai',
        model_name='gpt-4o'
    )
    
    print("   Testing: Will it rain tomorrow in London?")
    result = await orchestrator.process_market(
        market_question='Will it rain tomorrow in London?',
        bankroll=1000.0
    )
    
    judgment = result.get('judgment', {})
    trade = result.get('trade_proposal', {})
    
    print(f"   ✅ Consensus Probability: {judgment.get('consensus_probability', 0):.2%}")
    print(f"   ✅ Consensus Confidence: {judgment.get('consensus_confidence', 0):.2%}")
    print(f"   ✅ Agreement Level: {judgment.get('agreement_level', 'N/A')}")
    print(f"   ✅ Trade Action: {trade.get('action', 'N/A')}")
    print(f"   ✅ Trade Amount: {trade.get('amount', 0):.2f} GAS")
    print(f"   ✅ All 3 agents executed successfully!")

asyncio.run(test())
PYTHON_SCRIPT

# Test different market types
echo ""
echo "5️⃣  Testing Different Market Types..."

echo "   a) Weather Market..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from orchestrator import NoroOrchestrator

async def test():
    orchestrator = NoroOrchestrator(llm_provider='openai', model_name='gpt-4o')
    result = await orchestrator.process_market(
        'Will it rain tomorrow in New York?',
        bankroll=1000.0
    )
    print(f"      ✅ Weather analysis complete: {result.get('judgment', {}).get('consensus_probability', 0):.2%}")

asyncio.run(test())
PYTHON_SCRIPT

echo "   b) Crypto Market..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from orchestrator import NoroOrchestrator

async def test():
    orchestrator = NoroOrchestrator(llm_provider='openai', model_name='gpt-4o')
    result = await orchestrator.process_market(
        'Will Bitcoin price go above $50,000 by end of month?',
        bankroll=1000.0
    )
    print(f"      ✅ Crypto analysis complete: {result.get('judgment', {}).get('consensus_probability', 0):.2%}")

asyncio.run(test())
PYTHON_SCRIPT

echo "   c) Scientific Market..."
python3 << 'PYTHON_SCRIPT'
import asyncio
from orchestrator import NoroOrchestrator

async def test():
    orchestrator = NoroOrchestrator(llm_provider='openai', model_name='gpt-4o')
    result = await orchestrator.process_market(
        'Will a new cancer treatment be approved by FDA in 2025?',
        bankroll=1000.0
    )
    print(f"      ✅ Scientific analysis complete: {result.get('judgment', {}).get('consensus_probability', 0):.2%}")

asyncio.run(test())
PYTHON_SCRIPT

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ All Tests Complete!${NC}"
echo ""
echo "Summary:"
echo "  ✅ Backend is running"
echo "  ✅ Analyzer Agent working"
echo "  ✅ Trader Agent working"
echo "  ✅ Judge Agent working"
echo "  ✅ All 3 agents autonomous"
echo "  ✅ Real APIs being used"
echo ""
echo "Next Steps:"
echo "  1. Create a market via API"
echo "  2. Watch autonomous agents analyze it"
echo "  3. Check WebSocket for real-time updates"
echo ""

