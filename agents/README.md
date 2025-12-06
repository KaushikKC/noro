# noro SpoonOS Agents

This directory contains the SpoonOS-based AI agents for noro prediction markets.

## Architecture

The system consists of three main components:

1. **Analyzer Agent** (`analyzer_agent.py`)
   - Fetches scientific papers from PubMed and arXiv
   - Analyzes evidence and generates probability predictions
   - Outputs: probability, confidence, evidence summary

2. **Trader Agent** (`trader_agent.py`)
   - Takes analysis results from Analyzer Agent
   - Fetches market data from Neo blockchain
   - Calculates optimal stake using Kelly Criterion
   - Outputs: trade action (BUY_YES/BUY_NO), amount, confidence

3. **Orchestrator** (`orchestrator.py`)
   - Coordinates Analyzer and Trader agents
   - Processes complete market analysis pipeline

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install SpoonOS SDK
pip install spoon-ai-sdk

# Install other dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`
- `NEO_RPC_URL` (default: http://localhost:20332)

### 3. Run Agents

#### Test Analyzer Agent
```bash
python analyzer_agent.py
```

#### Test Trader Agent
```bash
python trader_agent.py
```

#### Run Full Pipeline
```bash
python orchestrator.py
```

## Usage

### Basic Usage

```python
import asyncio
from orchestrator import NoroOrchestrator

async def main():
    orchestrator = NoroOrchestrator(
        llm_provider="openai",
        model_name="gpt-4o"
    )
    
    result = await orchestrator.process_market(
        market_question="Will a new cancer treatment be approved by FDA in 2025?",
        bankroll=1000.0
    )
    
    print(result)

asyncio.run(main())
```

### Batch Processing

```python
orchestrator = NoroOrchestrator()

results = await orchestrator.batch_process([
    "Will AI achieve AGI by 2026?",
    "Will quantum computing break RSA by 2025?",
    "Will fusion energy be commercialized by 2030?"
], bankroll=3000.0)
```

## Tools

The agents use the following tools:

- **PubMedTool**: Search PubMed for scientific papers
- **ArxivTool**: Search arXiv for preprints and papers
- **NeoRPCTool**: Interact with Neo blockchain RPC
- **KellyCriterionTool**: Calculate optimal stake using Kelly Criterion
- **ConfidenceStakeTool**: Calculate stake based on confidence

## Output Format

### Analyzer Agent Output
```json
{
    "probability": 0.75,
    "confidence": 0.85,
    "evidence": "Summary of key findings...",
    "sources_count": 15,
    "market_question": "..."
}
```

### Trader Agent Output
```json
{
    "action": "BUY_YES",
    "amount": 500.0,
    "confidence": 0.92,
    "reasoning": "Explanation of trade decision...",
    "analysis": {...}
}
```

### Orchestrator Output
```json
{
    "market_question": "...",
    "market_id": "...",
    "analysis": {...},
    "trade_proposal": {...},
    "summary": {
        "probability": 0.75,
        "recommended_action": "BUY_YES",
        "recommended_stake": 500.0,
        "overall_confidence": 0.92
    }
}
```

## Configuration

### LLM Providers

Supported providers:
- `openai` - OpenAI models (GPT-4, GPT-4o, etc.)
- `anthropic` - Anthropic models (Claude Sonnet, etc.)
- `gemini` - Google Gemini models
- `deepseek` - DeepSeek models
- `openrouter` - OpenRouter (access to multiple providers)

### Neo RPC Configuration

Set `NEO_RPC_URL` in `.env`:
- Testnet: `http://localhost:20332` (default)
- Mainnet: Your mainnet RPC endpoint

## Troubleshooting

### Import Errors

If you see import errors for `spoon_ai`, make sure you've installed the SDK:
```bash
pip install spoon-ai-sdk
```

### API Key Errors

Make sure your `.env` file has at least one API key set:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

### Neo RPC Errors

If Neo RPC calls fail:
1. Check that your Neo node is running
2. Verify `NEO_RPC_URL` in `.env`
3. Test RPC endpoint: `curl http://localhost:20332 -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"getblockcount","params":[],"id":1}'`

## Next Steps

- Integrate with Neo smart contracts for actual trading
- Add more data sources (news, social media, etc.)
- Implement Judge Agent for multi-agent consensus
- Add state persistence for tracking trades
- Implement risk management and portfolio optimization

