"""
PredictX Backend API
FastAPI server that bridges frontend, agents, and Neo blockchain
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add agents directory to path for agent imports (used by agent_service)
agents_path = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(agents_path))

# Import backend modules (from current directory)
# These are in the same directory as main.py
from neo_rpc_client import NeoRPCClient
from neo_contract_client import NeoContractClient
from neo_oracle_client import NeoOracleClient, OracleWebhookHandler
from neofs_client import NeoFSClient
from agent_service import AgentService

# Load environment variables
load_dotenv()

# Configuration
NEO_RPC_URL = os.getenv("NEO_RPC_URL", "http://localhost:20332")
NEO_CONTRACT_HASH = os.getenv("NEO_CONTRACT_HASH", "0x32a4a922a9385c066a13cf82e79dafe9b2151f2a")
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")  # 'mainnet' or 'testnet'
NEOFS_ENDPOINT = os.getenv("NEOFS_ENDPOINT", "https://rest.fs.neo.org")
NEO_NETWORK_FS = os.getenv("NEO_NETWORK", "testnet")  # For NeoFS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize services
neo_client = NeoRPCClient(NEO_RPC_URL)
contract_client = NeoContractClient(NEO_RPC_URL, NEO_CONTRACT_HASH, network=NEO_NETWORK)
oracle_client = NeoOracleClient(NEO_RPC_URL)
oracle_handler = OracleWebhookHandler(contract_client, oracle_client)

# Initialize NeoFS client (may fail if spoon-ai-sdk not installed)
try:
    neofs_client = NeoFSClient(gateway_url=NEOFS_ENDPOINT, network=NEO_NETWORK_FS)
except ImportError as e:
    print(f"Warning: NeoFS client not available: {e}")
    neofs_client = None

agent_service = AgentService()

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, market_id: str):
        await websocket.accept()
        if market_id not in self.active_connections:
            self.active_connections[market_id] = []
        self.active_connections[market_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, market_id: str):
        if market_id in self.active_connections:
            self.active_connections[market_id].remove(websocket)
    
    async def broadcast(self, market_id: str, message: dict):
        if market_id in self.active_connections:
            for connection in self.active_connections[market_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# Background task for autonomous agent execution
async def autonomous_agent_scheduler():
    """
    Autonomous agent scheduler - runs agents automatically
    - Analyzes new markets when created
    - Re-analyzes open markets periodically
    """
    print("🤖 Starting autonomous agent scheduler...")
    
    while True:
        try:
            # Get all open markets from contract
            markets = await contract_client.get_all_markets()
            open_markets = [m for m in markets if not m.get("is_resolved", False)]
            
            print(f"📊 Found {len(open_markets)} open markets to analyze")
            
            # Analyze each open market
            for market in open_markets:
                market_id = market.get("id")
                market_question = market.get("question")
                
                if not market_id or not market_question:
                    continue
                
                try:
                    print(f"🔍 Auto-analyzing market {market_id}: {market_question[:50]}...")
                    
                    # Run full autonomous analysis (Analyzer + Trader + Judge)
                    result = await agent_service.full_analysis(
                        market_question=market_question,
                        market_id=market_id
                    )
                    
                    # Broadcast to WebSocket clients
                    await manager.broadcast(market_id, {
                        "type": "autonomous_analysis",
                        "data": result
                    })
                    
                    # Store in NeoFS if available
                    if neofs_client:
                        try:
                            await neofs_client.upload_agent_analysis(
                                container_id="predictx-markets",
                                market_id=market_id,
                                analysis=result
                            )
                        except Exception as e:
                            print(f"Failed to store in NeoFS: {e}")
                    
                    print(f"✅ Auto-analysis complete for market {market_id}")
                    
                except Exception as e:
                    print(f"❌ Error analyzing market {market_id}: {e}")
            
            # Wait before next cycle (1 hour = 3600 seconds)
            await asyncio.sleep(3600)
            
        except Exception as e:
            print(f"❌ Error in autonomous scheduler: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry


# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting PredictX Backend API...")
    print(f"📡 Neo RPC: {NEO_RPC_URL}")
    print(f"📄 Contract: {NEO_CONTRACT_HASH}")
    print(f"🌐 Network: {NEO_NETWORK}")
    
    # Start autonomous agent scheduler
    scheduler_task = asyncio.create_task(autonomous_agent_scheduler())
    print("✅ Autonomous agent scheduler started")
    
    yield
    
    # Shutdown
    print("👋 Shutting down PredictX Backend API...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    
    # Close client sessions
    await contract_client.close()
    await oracle_client.close()

# Create FastAPI app
app = FastAPI(
    title="PredictX API",
    description="Backend API for PredictX prediction markets",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MarketCreate(BaseModel):
    question: str
    description: str
    category: str
    resolve_date: str
    oracle_url: str
    initial_liquidity: float

class TradeProposal(BaseModel):
    market_id: str
    action: str  # "BUY_YES" or "BUY_NO"
    amount: float
    confidence: float

class MarketResponse(BaseModel):
    id: str
    question: str
    description: str
    category: str
    resolve_date: str
    creator: str
    created_at: str
    yes_shares: float
    no_shares: float
    is_resolved: bool
    outcome: Optional[str] = None

# Health check
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "PredictX API",
        "version": "0.1.0"
    }

@app.get("/health")
async def health():
    # Check Neo RPC connection
    try:
        block_count = await neo_client.get_block_count()
        neo_status = "connected"
    except:
        neo_status = "disconnected"
        block_count = 0
    
    return {
        "status": "ok",
        "neo_rpc": neo_status,
        "block_count": block_count,
        "contract_hash": NEO_CONTRACT_HASH
    }

# Market endpoints
@app.post("/markets/create")
async def create_market(market: MarketCreate, background_tasks: BackgroundTasks):
    """
    Create a new prediction market
    Returns transaction data for frontend to sign
    Also triggers autonomous agent analysis
    """
    try:
        # Convert resolve_date string to Unix timestamp
        from datetime import datetime
        resolve_timestamp = int(datetime.fromisoformat(market.resolve_date.replace('Z', '+00:00')).timestamp())
        
        # Prepare contract invocation using contract client
        tx_data = await contract_client.prepare_create_market_tx(
            question=market.question,
            description=market.description,
            category=market.category,
            resolve_date=resolve_timestamp,
            oracle_url=market.oracle_url
        )
        
        return {
            "success": True,
            "tx_data": tx_data,
            "message": "Transaction prepared. Sign with NeoLine wallet."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/markets")
async def list_markets():
    """
    List all markets from blockchain
    """
    try:
        # Get market count
        market_count = await contract_client.get_market_count()
        
        # Fetch each market
        markets = []
        for i in range(1, market_count + 1):
            market = await contract_client.get_market(str(i))
            if market:
                markets.append(market)
        
        return {
            "success": True,
            "markets": markets,
            "count": len(markets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/markets/{market_id}")
async def get_market(market_id: str):
    """
    Get market details by ID
    """
    try:
        market = await contract_client.get_market(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Get probability
        probability = await contract_client.get_probability(market_id)
        market["probability"] = probability
        
        return {
            "success": True,
            "market": market
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Agent endpoints
@app.post("/markets/{market_id}/analyze")
async def analyze_market(market_id: str):
    """
    Trigger agent analysis for a market
    """
    try:
        # Get market question using contract client
        market = await contract_client.get_market(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Run analyzer agent
        analysis = await agent_service.analyze_market(market["question"])
        
        # Store analysis in NeoFS if available
        if neofs_client:
            try:
                # Use market_id as container identifier or create one
                container_id = f"predictx-markets"
                await neofs_client.upload_agent_analysis(
                    container_id=container_id,
                    market_id=market_id,
                    analysis=analysis
                )
            except Exception as e:
                print(f"Failed to store analysis in NeoFS: {e}")
        
        # Broadcast to WebSocket clients
        await manager.broadcast(market_id, {
            "type": "analysis",
            "data": analysis
        })
        
        return {
            "success": True,
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/markets/{market_id}/trade/propose")
async def propose_trade(market_id: str, trade: TradeProposal):
    """
    Get trade proposal from Trader agent
    """
    try:
        # Get market data using contract client
        market = await contract_client.get_market(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Run trader agent
        trade_proposal = await agent_service.propose_trade(
            market_id=market_id,
            market_question=market["question"],
            analysis=trade.dict() if hasattr(trade, 'dict') else trade
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast(market_id, {
            "type": "trade_proposal",
            "data": trade_proposal
        })
        
        return {
            "success": True,
            "trade_proposal": trade_proposal
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/markets/{market_id}/trade/execute")
async def execute_trade(market_id: str, trade: TradeProposal):
    """
    Prepare trade transaction for frontend to sign
    """
    try:
        # Convert amount to smallest unit (GAS has 8 decimals)
        amount_smallest = int(trade.amount * 100000000)
        
        # Determine side from action
        side = "yes" if trade.action == "BUY_YES" else "no"
        
        tx_data = await contract_client.prepare_trade_tx(
            market_id=market_id,
            side=side,
            amount=amount_smallest
        )
        
        return {
            "success": True,
            "tx_data": tx_data,
            "message": "Transaction prepared. Sign with NeoLine wallet."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Oracle endpoints
@app.post("/markets/{market_id}/resolve/request")
async def request_market_resolution(
    market_id: str,
    oracle_url: str,
    filter: str = "$.outcome",
    gas_for_response: Optional[int] = None
):
    """
    Request Oracle resolution for a market
    
    According to Neo Oracle documentation:
    - Oracle.Request(url, filter, callback, userData, gasForResponse)
    - url: max 256 bytes, must return JSON with Content-Type: application/json
    - filter: JSONPath expression, max 128 bytes (e.g., "$.outcome")
    - callback: "onOracleCallback" (handled by contract)
    - userData: marketId as bytes
    - gasForResponse: minimum 0.1 GAS (10000000)
    
    Returns transaction data for frontend to sign
    """
    try:
        # Verify market exists
        market = await contract_client.get_market(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Validate Oracle URL
        url_validation = oracle_client.validate_oracle_url(oracle_url)
        if not url_validation.get("valid"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid Oracle URL: {url_validation.get('error', 'Unknown error')}"
            )
        
        # Prepare Oracle request transaction
        tx_data = await oracle_client.prepare_market_resolution_request(
            contract_hash=NEO_CONTRACT_HASH,
            market_id=market_id,
            oracle_url=oracle_url,
            filter=filter,
            gas_for_response=gas_for_response
        )
        
        # Get Oracle price for information
        oracle_price = await oracle_client.get_oracle_price()
        
        return {
            "success": True,
            "tx_data": tx_data,
            "oracle_info": {
                "request_fee": f"{oracle_price} GAS",
                "callback_fee": f"{tx_data['args'][3]['value'] / 100000000} GAS",
                "total_fee": f"{oracle_price + (tx_data['args'][3]['value'] / 100000000)} GAS",
                "url_scheme": url_validation.get("scheme"),
                "filter": filter
            },
            "message": "Oracle request prepared. Sign with NeoLine wallet."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/oracle/callback")
async def oracle_callback(request_data: dict):
    """
    Handle Oracle callback (webhook endpoint)
    This would be called by the Oracle service when data is fetched
    """
    try:
        request_id = request_data.get("request_id")
        market_id = request_data.get("user_data")  # market_id is passed as user_data
        oracle_result = request_data.get("result", "")
        
        # Process Oracle callback
        result = await oracle_handler.handle_oracle_callback(
            request_id=request_id,
            market_id=market_id,
            oracle_result=oracle_result
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NeoFS endpoints
@app.post("/neofs/containers/create")
async def create_neofs_container(name: str):
    """
    Create a NeoFS container
    """
    if not neofs_client:
        raise HTTPException(status_code=503, detail="NeoFS client not configured")
    
    try:
        container = await neofs_client.create_container(name)
        return {
            "success": True,
            "container": container
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/neofs/containers")
async def list_neofs_containers():
    """
    List NeoFS containers
    """
    if not neofs_client:
        raise HTTPException(status_code=503, detail="NeoFS client not configured")
    
    try:
        containers = await neofs_client.list_containers()
        return {
            "success": True,
            "containers": containers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/neofs/upload")
async def upload_to_neofs(
    container_id: str,
    object_name: str,
    data: bytes
):
    """
    Upload data to NeoFS
    """
    if not neofs_client:
        raise HTTPException(status_code=503, detail="NeoFS client not configured")
    
    try:
        result = await neofs_client.upload_object(
            container_id=container_id,
            object_name=object_name,
            data=data
        )
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time agent logs
@app.websocket("/ws/agent-logs/{market_id}")
async def agent_logs_stream(websocket: WebSocket, market_id: str):
    await manager.connect(websocket, market_id)
    try:
        while True:
            # Keep connection alive and send periodic updates
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, market_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

