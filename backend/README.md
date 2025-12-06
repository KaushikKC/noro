# PredictX Backend API

FastAPI backend that bridges the frontend, SpoonOS agents, and Neo blockchain.

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your configuration
```

## Configuration

Edit `.env` file:

```bash
# Neo Blockchain
NEO_RPC_URL=http://localhost:20332
NEO_CONTRACT_HASH=0x32a4a922a9385c066a13cf82e79dafe9b2151f2a

# LLM API Keys (for agents)
OPENAI_API_KEY=your_key_here
```

## Running

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check with Neo RPC status

### Markets
- `POST /markets/create` - Create new market (returns tx data for signing)
- `GET /markets` - List all markets
- `GET /markets/{id}` - Get market details

### Agents
- `POST /markets/{id}/analyze` - Trigger agent analysis
- `POST /markets/{id}/trade/propose` - Get trade proposal from agent
- `POST /markets/{id}/trade/execute` - Prepare trade transaction

### WebSocket
- `WS /ws/agent-logs/{market_id}` - Real-time agent logs

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test market creation
curl -X POST http://localhost:8000/markets/create \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will AI achieve AGI by 2026?",
    "description": "Test market",
    "category": "AI",
    "resolve_date": "2026-12-31",
    "oracle_url": "pubmed",
    "initial_liquidity": 10.0
  }'
```

## Architecture

```
Frontend (Next.js)
    ↓ HTTP/WebSocket
Backend API (FastAPI)
    ↓
    ├─► Neo RPC Client ──► Neo Blockchain
    └─► Agent Service ──► SpoonOS Agents
```

## Next Steps

1. Implement proper Neo contract method calls
2. Add database for market metadata
3. Add authentication
4. Add rate limiting
5. Add logging and monitoring

