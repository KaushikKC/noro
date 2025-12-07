# Noro - Decentralized Prediction Markets with AI-Powered Analysis

**The first prediction market platform that combines SpoonOS AI agents with Neo blockchain**

[![Neo Blockchain](https://img.shields.io/badge/Neo-N3-blue)](https://neo.org)
[![SpoonOS](https://img.shields.io/badge/SpoonOS-AI%20Agents-purple)](https://spoonos.ai)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#-features) • [Demo](#-demo) • [Architecture](#-architecture) • [Setup](#-getting-started) • [Documentation](#-documentation)

</div>

---

## Overview

Noro is a fully decentralized prediction market platform built on the Neo N3 blockchain. It leverages SpoonOS AI agents to provide intelligent market analysis, automated trading recommendations, and evidence-based probability predictions. The platform combines blockchain technology, decentralized storage (NeoFS), and advanced multi-agent AI systems to create a sophisticated prediction market ecosystem.

### What Makes Noro Unique?

- **AI-Powered Analysis**: Three specialized SpoonOS agents (Analyzer, Trader, Judge) automatically research scientific papers, analyze evidence, and generate probability predictions
- **Fully Decentralized**: Built on Neo blockchain with NeoFS storage - markets are immutable, transparent, and censorship-resistant
- **Evidence-Based Trading**: Trade recommendations backed by real scientific research from PubMed and arXiv, not speculation
- **Automated Resolution**: Neo Oracle integration automatically resolves markets when events occur
- **Real-Time Updates**: WebSocket connections provide live agent activity and market updates
- **Risk Management**: Trader agent uses Kelly Criterion for optimal stake sizing

---

## Demo

### Live Demo Links

- **Production Demo**: [Link](https://youtu.be/yTx7O7zlua0)

### Quick Demo Access

If you have deployed instances, add them here:
- Frontend URL: `https://your-frontend-url.com`
- Backend API: `https://your-api-url.com`
- Smart Contract: `0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a` (Neo Testnet)

---

## ✨ Features

### Core Features

- ✅ **Market Creation**: Create prediction markets with questions, descriptions, categories, and resolve dates
- ✅ **Trading**: Buy YES or NO shares using GAS tokens
- ✅ **AI Analysis**: Automatic market analysis by SpoonOS agents
- ✅ **Oracle Resolution**: Automated market resolution via Neo Oracle
- ✅ **Decentralized Storage**: Market metadata stored on NeoFS
- ✅ **Real-Time Updates**: WebSocket connections for live updates
- ✅ **Wallet Integration**: Seamless NeoLine wallet integration

### AI Agent Capabilities

1. **Analyzer Agent**
   - Searches PubMed and arXiv for scientific papers
   - Analyzes evidence and generates probability predictions
   - Provides confidence scores and evidence summaries

2. **Trader Agent**
   - Fetches real-time market data from Neo blockchain
   - Calculates optimal stakes using Kelly Criterion
   - Generates trade recommendations (BUY_YES/BUY_NO)

3. **Judge Agent**
   - Aggregates multiple analyses for consensus
   - Provides weighted probability estimates
   - Validates market outcomes

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Market Pages │  │ Agent Chat    │  │ Trade Panel  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│              Backend API (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Neo RPC Client│  │ Agent Service│  │ NeoFS Client │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└──────────┬───────────────────┬───────────────────┬──────────┘
           │                   │                   │
    ┌──────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐
    │ Neo N3      │   │ SpoonOS       │   │ NeoFS        │
    │ Blockchain  │   │ AI Agents     │   │ Storage      │
    └─────────────┘   └───────────────┘   └──────────────┘
```

### Technology Stack

**Frontend**
- Next.js 16
- TypeScript
- React 19
- Tailwind CSS
- NeoLine Wallet Integration

**Backend**
- FastAPI (Python)
- WebSocket Support
- SQLite Database
- Neo RPC Client

**Blockchain**
- Neo N3 Smart Contracts (C#)
- Neo Oracle Integration
- NeoFS Decentralized Storage

**AI Agents**
- SpoonOS SDK
- ToolCallAgent Architecture
- Multiple LLM Providers (OpenAI, Anthropic, Gemini)

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.12+
- Neo N3 wallet (NeoLine)
- LLM API Key (OpenAI, Anthropic, or Gemini)
- Neo RPC access (testnet or mainnet)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/predictx.git
cd predictx
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your configuration
```

**Backend Environment Variables** (`.env`):
```bash
# Neo Blockchain
NEO_RPC_URL=https://testnet1.neo.coz.io:443
NEO_CONTRACT_HASH=0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a
NEO_NETWORK=testnet

# NeoFS
NEOFS_ENDPOINT=https://rest.fs.neo.org
NEOFS_OWNER_ADDRESS=your_address_here
NEOFS_PRIVATE_KEY_WIF=your_wif_here
NEOFS_PUBLIC_CONTAINER_ID=CeeroywT8ppGE4HGjhpzocJkdb2yu3wD5qCGFTjkw1Cc

# LLM API Keys (at least one required)
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.0-flash-exp
```

#### 3. Agents Setup

```bash
cd agents

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install SpoonOS SDK
pip install spoon-ai-sdk

# Copy environment file
cp env.template .env
# Edit .env and add your API keys
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install

# Copy environment file
cp .env.example .env.local
# Edit .env.local and add your configuration
```

**Frontend Environment Variables** (`.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_NEO_RPC_URL=https://testnet1.neo.coz.io:443
NEXT_PUBLIC_CONTRACT_HASH=0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a
```

#### 5. Smart Contract Setup

See [contracts/README.md](contracts/README.md) for detailed instructions on building and deploying the smart contract.

### Running the Application

#### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📚 Documentation

### Project Structure

```
noro/
├── agents/              # SpoonOS AI agents
│   ├── analyzer_agent.py
│   ├── trader_agent.py
│   ├── judge_agent.py
│   ├── orchestrator.py
│   └── tools/           # Custom tools for agents
├── backend/             # FastAPI backend
│   ├── main.py         # Main API server
│   ├── neo_rpc_client.py
│   ├── neo_contract_client.py
│   ├── neofs_client.py
│   └── agent_service.py
├── contracts/          # Neo N3 smart contracts
│   └── PredictXMarket.cs
├── frontend/           # Next.js frontend
│   └── src/
│       ├── app/       # Next.js app router
│       ├── components/
│       └── lib/
└── README.md
```

### API Documentation

#### Market Endpoints

- `POST /markets/create` - Create a new prediction market
- `GET /markets` - List all markets
- `GET /markets/{id}` - Get market details

#### Agent Endpoints

- `POST /markets/{id}/analyze` - Trigger agent analysis
- `POST /markets/{id}/trade/propose` - Get trade proposal
- `POST /markets/{id}/trade/execute` - Execute trade

#### WebSocket

- `WS /ws/agent-logs/{market_id}` - Real-time agent logs

See [backend/README.md](backend/README.md) for complete API documentation.

### Smart Contract Methods

- `createMarket(question, description, category, resolveDate, oracleUrl)` - Create market
- `buyYes(marketId, amount)` - Buy YES shares
- `buyNo(marketId, amount)` - Buy NO shares
- `getProbability(marketId)` - Get current probability
- `requestResolve(marketId, oracleUrl, filter, callbackMethod)` - Request resolution
- `payout(marketId)` - Distribute payouts

See [contracts/README.md](contracts/README.md) for complete contract documentation.

---

## Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Create market
curl -X POST http://localhost:8000/markets/create \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Will AI achieve AGI by 2026?",
    "description": "Test market",
    "category": "AI",
    "resolve_date": "2026-12-31T23:59:59Z",
    "oracle_url": "pubmed",
    "initial_liquidity": 10.0
  }'
```

### Test Agents

```bash
cd agents
python orchestrator.py
```

### Sample Market Data

See [SAMPLE_MARKET_DATA.txt](SAMPLE_MARKET_DATA.txt) and [sample_markets.json](sample_markets.json) for ready-to-use market examples.

---

## Use Cases

Noro is perfect for:

- **Medical Research**: FDA approvals, clinical trial outcomes, treatment efficacy
- **Technology**: Quantum computing milestones, AI breakthroughs, hardware innovations
- **Climate Science**: Temperature records, weather patterns, environmental events
- **Energy**: Fusion milestones, renewable energy adoption, energy policy impacts
- **Scientific Research**: Breakthrough discoveries, research milestones, publication predictions

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Neo Blockchain](https://neo.org) - For the amazing blockchain platform
- [SpoonOS](https://spoonos.ai) - For the powerful AI agent framework
- [NeoFS](https://fs.neo.org) - For decentralized storage
- All contributors and the open-source community

---

## Contact & Support

- **Project Repository**: [GitHub](https://github.com/yourusername/predictx)
- **Issues**: [GitHub Issues](https://github.com/yourusername/predictx/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/predictx/wiki)

---

## Roadmap

- [ ] Enhanced security and access control
- [ ] More sophisticated risk management
- [ ] Additional data sources for agents
- [ ] Portfolio optimization across markets
- [ ] Advanced oracle integration
- [ ] Mobile application
- [ ] Social features and market sharing
- [ ] Analytics dashboard for traders

---

<div align="center">

**Built with for the Neo and SpoonOS communities**

⭐ Star this repo if you find it helpful!

</div>

