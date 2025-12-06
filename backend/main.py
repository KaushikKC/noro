"""
noro Backend API
FastAPI server that bridges frontend, agents, and Neo blockchain
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request
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
from database import insert_market, get_market as get_market_from_db, list_markets as list_markets_from_db, update_market_onchain_data

# Load environment variables
load_dotenv()

# Configuration
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")  # 'mainnet' or 'testnet'

# Set default RPC URL based on network if not provided
_default_rpc_url = (
    "https://mainmagnet.ngd.network:443" if NEO_NETWORK == "mainnet"
    else "https://testnet1.neo.coz.io:443"  # Updated to use coz.io testnet RPC
)
NEO_RPC_URL = os.getenv("NEO_RPC_URL", _default_rpc_url)
# Use same contract hash as frontend
# Frontend uses: 0x1974aac54640ec80413e2229003b617daf849a13
NEO_CONTRACT_HASH = os.getenv("NEO_CONTRACT_HASH", "0x1974aac54640ec80413e2229003b617daf849a13")
# NeoFS endpoint - should NOT include /v1 (client adds it)
NEOFS_ENDPOINT = os.getenv("NEOFS_ENDPOINT", "https://rest.fs.neo.org")
# Remove /v1 suffix if present (the client adds it automatically)
if NEOFS_ENDPOINT.endswith('/v1'):
    NEOFS_ENDPOINT = NEOFS_ENDPOINT[:-3]

# Public NeoFS container ID (provided by Neo team)
# This is a public container that doesn't require balance to use
NEOFS_PUBLIC_CONTAINER_ID = os.getenv("NEOFS_PUBLIC_CONTAINER_ID", "CeeroywT8ppGE4HGjhpzocJkdb2yu3wD5qCGFTjkw1Cc")
NEO_NETWORK_FS = os.getenv("NEO_NETWORK", "testnet")  # For NeoFS
# NeoFS requires owner_address and private_key_wif for operations
# These match the environment variable names expected by NeoFSClient in spoon-ai-sdk:
# NEOFS_BASE_URL, NEOFS_OWNER_ADDRESS, NEOFS_PRIVATE_KEY_WIF
NEOFS_OWNER_ADDRESS = os.getenv("NEOFS_OWNER_ADDRESS", "")
NEOFS_PRIVATE_KEY_WIF = os.getenv("NEOFS_PRIVATE_KEY_WIF", "")
# Set NEOFS_BASE_URL (required by NeoFSClient, alias for NEOFS_ENDPOINT)
if not os.getenv("NEOFS_BASE_URL"):
    os.environ["NEOFS_BASE_URL"] = NEOFS_ENDPOINT
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize services (lazy initialization for async clients)
# Use testnet RPC if localhost is specified
_rpc_url = NEO_RPC_URL if NEO_RPC_URL != "http://localhost:20332" else _default_rpc_url
neo_client = NeoRPCClient(_rpc_url)
# Contract and oracle clients will be initialized in lifespan
contract_client = None
oracle_client = None
oracle_handler = None

# Initialize NeoFS client (may fail if spoon-ai-sdk not installed or other errors)
neofs_client = None
try:
    print(f"🔧 Initializing NeoFS client...")
    print(f"   Gateway: {NEOFS_ENDPOINT}")
    print(f"   Network: {NEO_NETWORK_FS}")
    print(f"   Owner Address: {NEOFS_OWNER_ADDRESS[:10] + '...' if NEOFS_OWNER_ADDRESS else 'NOT SET'}")
    print(f"   Private Key: {'SET' if NEOFS_PRIVATE_KEY_WIF else 'NOT SET'}")
    
    if not NEOFS_OWNER_ADDRESS or not NEOFS_PRIVATE_KEY_WIF:
        print(f"⚠️  Warning: NeoFS owner_address or private_key_wif not set in .env")
        print(f"   NeoFS operations will fail. Set NEOFS_OWNER_ADDRESS and NEOFS_PRIVATE_KEY_WIF in backend/.env")
        print(f"   For now, NeoFS client will be initialized but operations may fail.")
    
    neofs_client = NeoFSClient(gateway_url=NEOFS_ENDPOINT, network=NEO_NETWORK_FS)
    print(f"✅ NeoFS client initialized successfully")
except ImportError as e:
    print(f"⚠️  Warning: NeoFS client not available (ImportError): {e}")
    print(f"   Install spoon-ai-sdk: pip install spoon-ai-sdk")
    neofs_client = None
except Exception as e:
    print(f"⚠️  Warning: NeoFS client initialization failed: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
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
            # Get all open markets from contract (if available)
            if contract_client:
                markets = await contract_client.get_all_markets()
            else:
                markets = []  # Skip if contract client not available
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
                                container_id=NEOFS_PUBLIC_CONTAINER_ID,
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


# Helper function to get NeoFS public container ID
async def get_neofs_container_id():
    """
    Get the NeoFS public container ID for storing market data
    Uses the public container provided by Neo team (no balance required)
    """
    if not neofs_client:
        print("⚠️  NeoFS client not available, using public container ID from config")
        return NEOFS_PUBLIC_CONTAINER_ID
    
    # Use the public container ID provided by Neo team
    # This is a public container that doesn't require balance to use
    container_id = NEOFS_PUBLIC_CONTAINER_ID
    print(f"📦 Using NeoFS public container: {container_id}")
    print(f"   This is a public container provided by Neo team")
    print(f"   No balance required - you can read/write to this container")
    
    # Optionally verify the container exists and is accessible
    try:
        container_info = await neofs_client.get_container_info(container_id)
        print(f"✅ Verified public container is accessible")
        if isinstance(container_info, dict):
            print(f"   Container info: {container_info}")
    except Exception as e:
        print(f"⚠️  Could not verify container info (but will still try to use it): {e}")
        # Continue anyway - the container might still be accessible
    
    return container_id

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global contract_client, oracle_client, oracle_handler
    
    print("🚀 Starting noro Backend API...")
    print(f"📡 Neo RPC: {NEO_RPC_URL}")
    print(f"📄 Contract: {NEO_CONTRACT_HASH}")
    print(f"🌐 Network: {NEO_NETWORK}")
    
    # Initialize async clients (requires event loop)
    try:
        # Use None for RPC URL to let NeoContractClient use its network-specific default
        # Or use the configured URL if it's not localhost
        rpc_url_for_client = None if NEO_RPC_URL == "http://localhost:20332" else NEO_RPC_URL
        contract_client = NeoContractClient(rpc_url_for_client, NEO_CONTRACT_HASH, network=NEO_NETWORK)
        oracle_client = NeoOracleClient(rpc_url_for_client or NEO_RPC_URL)
        oracle_handler = OracleWebhookHandler(contract_client, oracle_client)
        print("✅ Neo clients initialized")
        print(f"📡 Using RPC URL: {contract_client.rpc_url}")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Neo clients: {e}")
        print("   Continuing with basic RPC client only...")
    
    # Ensure NeoFS container exists
    neofs_container_id = await get_neofs_container_id()
    if neofs_container_id:
        # Store container ID globally for use in endpoints
        import os
        os.environ["NEOFS_CONTAINER_ID"] = neofs_container_id
    
    # Start autonomous agent scheduler
    scheduler_task = asyncio.create_task(autonomous_agent_scheduler())
    print("✅ Autonomous agent scheduler started")
    
    yield
    
    # Shutdown
    print("👋 Shutting down noro Backend API...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    
    # Close client sessions
    if contract_client:
        try:
            await contract_client.close()
        except:
            pass
    if oracle_client:
        try:
            await oracle_client.close()
        except:
            pass

# Create FastAPI app
app = FastAPI(
    title="noro API",
    description="Backend API for noro prediction markets",
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

class AnalyzeTestRequest(BaseModel):
    question: str
    oracle_url: Optional[str] = ""
    market_id: Optional[str] = "test"

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
        "service": "noro API",
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
    Also stores market data in NeoFS and triggers autonomous agent analysis
    """
    try:
        # Convert resolve_date string to Unix timestamp
        from datetime import datetime
        resolve_timestamp = int(datetime.fromisoformat(market.resolve_date.replace('Z', '+00:00')).timestamp())
        
        # Prepare contract invocation using contract client
        if not contract_client:
            raise HTTPException(status_code=503, detail="Contract client not initialized")
        
        tx_data = await contract_client.prepare_create_market_tx(
            question=market.question,
            description=market.description,
            category=market.category,
            resolve_date=resolve_timestamp,
            oracle_url=market.oracle_url
        )
        
        # Prepare market data for NeoFS storage (will be stored after transaction confirmation)
        market_data = {
            "question": market.question,
            "description": market.description,
            "category": market.category,
            "resolve_date": market.resolve_date,
            "resolve_timestamp": resolve_timestamp,
            "oracle_url": market.oracle_url,
            "initial_liquidity": market.initial_liquidity,
            "created_at": datetime.now().isoformat(),
            "created_timestamp": int(datetime.now().timestamp()),
            "status": "pending",  # Will be updated after transaction confirmation
            "source": "contract_creation"
        }
        
        # Schedule background task to store in NeoFS after transaction
        # This will wait for transaction confirmation and get the actual market_id
        background_tasks.add_task(
            store_market_data_in_neofs_after_tx,
            market_data=market_data,
            tx_data=tx_data
        )
        
        return {
            "success": True,
            "tx_data": tx_data,
            "message": "Transaction prepared. Sign with NeoLine wallet.",
            "neofs_storage": "Market data stored in NeoFS (will be updated with market_id after transaction confirmation)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def store_market_data_in_neofs_after_tx(market_data: dict, tx_data: dict):
    """
    Background task to store market data in NeoFS after transaction confirmation
    
    Args:
        market_data: Market data dictionary
        tx_data: Transaction data from prepare_create_market_tx
    """
    if not neofs_client:
        print("⚠️  NeoFS client not available, skipping storage")
        return
    
    try:
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", NEOFS_PUBLIC_CONTAINER_ID)
        
        # Wait for transaction to be confirmed (poll for market count increase)
        print(f"⏳ Waiting for transaction confirmation to get market_id...")
        max_attempts = 30  # Wait up to 30 seconds
        market_id = None
        
        for attempt in range(max_attempts):
            await asyncio.sleep(1)  # Wait 1 second between attempts
            
            if contract_client:
                try:
                    # Get current market count
                    count = await contract_client.get_market_count()
                    print(f"  📊 Attempt {attempt + 1}/{max_attempts}: Market count = {count}")
                    
                    if count > 0:
                        # The new market should be the latest one
                        market_id = str(count)
                        
                        # Verify the market exists and matches our question
                        try:
                            contract_market = await contract_client.get_market(market_id)
                            if contract_market and contract_market.get("question") == market_data.get("question"):
                                print(f"✅ Found matching market in contract: {market_id}")
                                break
                        except:
                            pass
                except Exception as e:
                    print(f"  ⚠️  Error checking market count: {e}")
        
        if not market_id:
            print(f"⚠️  Could not determine market_id after {max_attempts} attempts")
            print(f"   Storing with pending status...")
            # Store with pending status
            import hashlib
            question_hash = hashlib.sha256(market_data.get("question", "").encode()).hexdigest()[:16]
            temp_market_id = f"pending_{question_hash}"
            
            result = await neofs_client.upload_market_data(
                container_id=container_id,
                market_id=temp_market_id,
                market_data=market_data
            )
            print(f"⚠️  Stored pending market data in NeoFS: {temp_market_id}")
            return
        
        # Update market data with confirmed status
        market_data["market_id"] = market_id
        market_data["status"] = "confirmed"
        if tx_data and "txid" in tx_data:
            market_data["tx_hash"] = tx_data["txid"]
        
        # Upload to NeoFS
        print(f"📦 Storing market {market_id} data to NeoFS container {container_id}...")
        result = await neofs_client.upload_market_data(
            container_id=container_id,
            market_id=market_id,
            market_data=market_data
        )
        
        if isinstance(result, dict):
            object_id = result.get("object_id") or result.get("id")
        else:
            object_id = str(result)
        
        print(f"✅ Successfully stored market {market_id} data in NeoFS")
        print(f"   Container: {container_id}")
        print(f"   Object ID: {object_id}")
        print(f"   Question: {market_data.get('question', 'N/A')[:50]}...")
        
    except Exception as e:
        print(f"❌ Error storing market data in NeoFS: {e}")
        import traceback
        traceback.print_exc()

async def store_market_data_in_neofs(market_data: dict, tx_hash: Optional[str] = None, market_id: Optional[str] = None):
    """
    Background task to store market data in NeoFS (legacy function, kept for compatibility)
    
    Args:
        market_data: Market data dictionary
        tx_hash: Transaction hash (optional)
        market_id: Market ID from contract (optional, will be fetched if not provided)
    """
    if not neofs_client:
        return
    
    try:
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", NEOFS_PUBLIC_CONTAINER_ID)
        
        # If market_id not provided, try to get it from contract after some delay
        if not market_id and tx_hash:
            # Wait a bit for transaction to be confirmed
            await asyncio.sleep(5)
            if contract_client:
                try:
                    # Try to get the latest market count to determine market_id
                    count = await contract_client.get_market_count()
                    market_id = str(count) if count > 0 else None
                except:
                    pass
        
        if market_id:
            market_data["market_id"] = market_id
            market_data["status"] = "confirmed"
            if tx_hash:
                market_data["tx_hash"] = tx_hash
            
            # Upload to NeoFS
            result = await neofs_client.upload_market_data(
                container_id=container_id,
                market_id=market_id,
                market_data=market_data
            )
            print(f"✅ Stored market {market_id} data in NeoFS: {result.get('object_id', 'unknown')}")
        else:
            # Store with pending status, will be updated later
            result = await neofs_client.upload_market_data(
                container_id=container_id,
                market_id=market_data.get("question", "pending"),
                market_data=market_data
            )
            print(f"⚠️  Stored pending market data in NeoFS (will be updated with market_id)")
    except Exception as e:
        print(f"❌ Error storing market data in NeoFS: {e}")

@app.get("/markets")
async def list_markets():
    """
    List all markets from database (fast retrieval)
    Enriches with contract data (shares, probabilities, etc.)
    """
    try:
        # Fetch from database (fast) - include both "active" and "confirmed" markets
        print(f"💾 [LIST] Fetching markets from database...")
        import sqlite3
        import os
        db_path = os.getenv("MARKET_DB_PATH", "markets.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM markets 
            WHERE status IN ('active', 'confirmed')
            ORDER BY created_timestamp DESC 
            LIMIT 100
        """)
        rows = cursor.fetchall()
        markets = [dict(row) for row in rows]
        conn.close()
        print(f"💾 [LIST] Found {len(markets)} markets in database")
        
        # Enrich with contract data if available (temporarily disabled due to parsing errors)
        # if contract_client and markets:
        #     try:
        #         market_count = await contract_client.get_market_count()
        #         if market_count > 0:
        #             print(f"📊 [LIST] Enriching with contract data ({market_count} markets on-chain)...")
        #             
        #             # Create lookup for contract data by market_id
        #             contract_data_map = {}
        #             for i in range(1, market_count + 1):
        #                 try:
        #                     contract_market = await contract_client.get_market(str(i))
        #                     if contract_market:
        #                         contract_data_map[str(i)] = contract_market
        #                 except:
        #                     continue
        #             
        #             # Update markets with contract data
        #             for market in markets:
        #                 market_id = str(market.get("market_id") or market.get("id") or "")
        #                 if market_id in contract_data_map:
        #                     contract_market = contract_data_map[market_id]
        #                     # Update database with latest contract data
        #                     update_market_onchain_data(market_id, {
        #                         "yes_shares": contract_market.get("yes_shares", 0),
        #                         "no_shares": contract_market.get("no_shares", 0),
        #                         "is_resolved": contract_market.get("resolved", False),
        #                         "outcome": contract_market.get("outcome"),
        #                         "probability": contract_market.get("probability", 50),
        #                     })
        #                     # Also update in-memory data for response
        #                     market.update({
        #                         "yes_shares": contract_market.get("yes_shares", 0),
        #                         "no_shares": contract_market.get("no_shares", 0),
        #                         "is_resolved": contract_market.get("resolved", False),
        #                         "outcome": contract_market.get("outcome"),
        #                         "probability": contract_market.get("probability", 50),
        #                     })
        #     except Exception as e:
        #         print(f"⚠️ [LIST] Contract enrichment error: {e}")
        
        # Convert SQLite Row objects to dicts for JSON serialization
        markets_list = []
        for market in markets:
            if hasattr(market, 'keys'):  # SQLite Row object
                market_dict = dict(market)
            else:
                market_dict = market
            
            # Ensure market_id is set for frontend (use market_id as id)
            if "market_id" in market_dict and "id" not in market_dict:
                market_dict["id"] = str(market_dict["market_id"])
            
            markets_list.append(market_dict)
        
        print(f"✅ [LIST] Returning {len(markets_list)} markets to frontend")
        return {
            "success": True,
            "markets": markets_list,
            "count": len(markets_list),
            "source": "database"
        }
    except Exception as e:
        print(f"❌ [LIST] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/markets/{market_id}/neofs/store")
async def store_market_in_neofs(market_id: str, request: Request):
    """
    Manually trigger storage of a market in NeoFS
    """
    print(f"📥 [STORE] POST /markets/{market_id}/neofs/store")
    try:
        if not neofs_client:
            print(f"❌ [STORE] NeoFS client not available")
            return {"success": False, "reason": "NeoFS client not available"}
        
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", NEOFS_PUBLIC_CONTAINER_ID)
        
        # Get market_data from request body (human-readable data from frontend)
        try:
            body = await request.json()
            market_data = body if body else None
            print(f"📥 [STORE] Received data: question='{market_data.get('question', 'N/A')[:40] if market_data else 'None'}...'")
        except Exception as e:
            print(f"❌ [STORE] Error parsing request: {e}")
            market_data = None
        
        # Market data MUST be provided from frontend (human-readable)
        if not market_data:
            print(f"❌ [STORE] No market data provided")
            return {
                "success": False,
                "reason": "Market data must be provided. Contract data is encoded and not human-readable."
            }
        
        # Validate required fields
        if not market_data.get("question"):
            print(f"❌ [STORE] Missing question field")
            return {"success": False, "reason": "Question is required"}
        
        # Add metadata
        from datetime import datetime
        market_data["market_id"] = market_id
        market_data["status"] = "confirmed"
        market_data["created_at"] = datetime.now().isoformat()
        market_data["created_timestamp"] = int(datetime.now().timestamp())
        market_data["source"] = "frontend_creation"
        
        # Convert resolveDate to resolve_date and resolve_timestamp if needed
        if "resolveDate" in market_data and "resolve_date" not in market_data:
            resolve_date_str = market_data.pop("resolveDate")
            # If it's a timestamp string, convert to both formats
            try:
                resolve_timestamp = int(resolve_date_str)
                market_data["resolve_timestamp"] = resolve_timestamp
                # Convert timestamp to ISO date string
                market_data["resolve_date"] = datetime.fromtimestamp(resolve_timestamp / 1000).isoformat()
            except:
                market_data["resolve_date"] = resolve_date_str
        
        # Handle oracleUrl -> oracle_url
        if "oracleUrl" in market_data and "oracle_url" not in market_data:
            market_data["oracle_url"] = market_data.pop("oracleUrl")
        
        print(f"📦 [STORE] Market {market_id} -> NeoFS container {container_id}")
        print(f"   Question: {market_data.get('question', 'N/A')[:50]}...")
        
        result = await neofs_client.upload_market_data(
            container_id=container_id,
            market_id=market_id,
            market_data=market_data
        )
        
        # Extract object_id from result (could be dict or string)
        object_id = None
        if isinstance(result, dict):
            object_id = result.get("object_id") or result.get("id") or result.get("oid")
        elif isinstance(result, str):
            # Try to extract object ID from formatted string
            import re
            oid_match = re.search(r'Object ID: ([A-Za-z0-9]+)', result)
            if oid_match:
                object_id = oid_match.group(1)
            else:
                object_id = result[:50]  # Fallback to first 50 chars
        
        print(f"✅ [STORE] Market {market_id} stored in NeoFS! Object ID: {object_id}")
        
        # Generate NeoFS download URL
        neofs_base_url = os.getenv("NEOFS_ENDPOINT", "https://rest.fs.neo.org")
        neofs_url = f"{neofs_base_url}/v1/objects/{container_id}/by_id/{object_id}" if object_id else None
        
        # Store in database for fast retrieval
        market_data["neofs_object_id"] = object_id
        market_data["neofs_container_id"] = container_id
        market_data["neofs_url"] = neofs_url
        
        print(f"💾 [STORE] Storing market {market_id} in database...")
        db_success = insert_market(market_data)
        if db_success:
            print(f"✅ [STORE] Market {market_id} stored in database!")
        else:
            print(f"⚠️ [STORE] Failed to store market {market_id} in database")
        
        return {
            "success": True,
            "market_id": market_id,
            "container_id": container_id,
            "object_id": object_id,
            "neofs_url": neofs_url,
            "message": f"Market {market_id} stored in NeoFS and database"
        }
    except Exception as e:
        print(f"❌ [STORE] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "reason": str(e)}

@app.get("/markets/{market_id}/neofs/verify")
async def verify_market_in_neofs(market_id: str):
    """
    Verify if a market exists in NeoFS storage
    
    Args:
        market_id: Market ID to check
        
    Returns:
        Dict with verification status and market data if found
    """
    try:
        if not neofs_client:
            return {
                "success": False,
                "in_neofs": False,
                "reason": "NeoFS client not available"
            }
        
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", NEOFS_PUBLIC_CONTAINER_ID)
        
        neofs_data = await neofs_client.get_market_data(
            container_id=container_id,
            market_id=market_id
        )
        
        if neofs_data:
            print(f"✅ Market {market_id} found in NeoFS")
            return {
                "success": True,
                "in_neofs": True,
                "market_id": market_id,
                "container_id": container_id,
                "market_data": {
                    "question": neofs_data.get("question", "N/A"),
                    "description": neofs_data.get("description", "N/A"),
                    "category": neofs_data.get("category", "N/A"),
                    "status": neofs_data.get("status", "unknown"),
                    "created_at": neofs_data.get("created_at", "N/A"),
                    "tx_hash": neofs_data.get("tx_hash", "N/A")
                }
            }
        else:
            print(f"⚠️ Market {market_id} NOT in NeoFS")
            return {
                "success": True,
                "in_neofs": False,
                "market_id": market_id,
                "container_id": container_id,
                "reason": "Market data not found in NeoFS. It may still be processing or the transaction hasn't been confirmed yet."
            }
    except Exception as e:
        print(f"❌ [VERIFY NEOFS] Error checking NeoFS: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "in_neofs": False,
            "error": str(e)
        }

@app.get("/neofs/status")
async def get_neofs_status():
    """
    Get NeoFS storage status and container information
    """
    try:
        if not neofs_client:
            return {
                "success": False,
                "available": False,
                "reason": "NeoFS client not available"
            }
        
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", NEOFS_PUBLIC_CONTAINER_ID)
        
        # List all markets in NeoFS
        markets = await neofs_client.list_all_markets(container_id=container_id)
        
        # Get container info
        try:
            container_info = await neofs_client.get_container_info(container_id)
        except:
            container_info = None
        
        return {
            "success": True,
            "available": True,
            "container_id": container_id,
            "container_info": container_info,
            "markets_count": len(markets),
            "markets": [
                {
                    "market_id": m.get("market_id", "unknown"),
                    "question": m.get("question", "N/A")[:50],
                    "status": m.get("status", "unknown")
                }
                for m in markets
            ]
        }
    except Exception as e:
        print(f"❌ [NEOFS STATUS] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "available": False,
            "error": str(e)
        }

@app.get("/markets/{market_id}")
async def get_market(market_id: str):
    """
    Get a single market by ID from database (fast retrieval)
    Enriches with contract data if available
    Shows NeoFS URL for downloading the original data
    """
    try:
        # Fetch from database (fast)
        print(f"💾 [GET] Fetching market {market_id} from database...")
        market = get_market_from_db(market_id)
        
        if not market:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
        
        # Enrich with contract data if available
        if contract_client:
            try:
                contract_market = await contract_client.get_market(market_id)
                if contract_market:
                    # Update database with latest contract data
                    update_market_onchain_data(market_id, {
                        "yes_shares": contract_market.get("yes_shares", 0),
                        "no_shares": contract_market.get("no_shares", 0),
                        "is_resolved": contract_market.get("resolved", False),
                        "outcome": contract_market.get("outcome"),
                        "probability": contract_market.get("probability", 50),
                    })
                    # Also update in-memory data for response
                    market.update({
                        "yes_shares": contract_market.get("yes_shares", 0),
                        "no_shares": contract_market.get("no_shares", 0),
                        "is_resolved": contract_market.get("resolved", False),
                        "outcome": contract_market.get("outcome"),
                        "probability": contract_market.get("probability", 50),
                    })
            except Exception as e:
                print(f"⚠️ [GET] Contract enrichment error: {e}")
        
        return {
            "success": True,
            "market": market,
            "source": "database" + ("+contract" if contract_client else "")
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [GET] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent endpoints
@app.post("/markets/{market_id}/analyze")
async def analyze_market(market_id: str):
    """
    Trigger FULL autonomous agent analysis for a market
    Runs: Analyzer → Trader → Judge (all 3 agents)
    Uses REAL APIs only - NO MOCK DATA
    """
    try:
        # Get market question using contract client
        if not contract_client:
            # Use agent service with just the question if contract not available
            result = await agent_service.full_analysis(
                market_question=f"Market {market_id}",
                market_id=market_id
            )
            return {
                "success": True,
                "analysis": result,
                "note": "Contract client not available, using direct analysis"
            }
        
        # Get market from database first (fast)
        print(f"🔍 [ANALYZE MARKET] Fetching market {market_id} from database...")
        market = get_market_from_db(market_id)
        
        if not market and contract_client:
            # Fallback to contract if not in database
            print(f"⚠️ [ANALYZE MARKET] Market {market_id} not in database, trying contract...")
            market = await contract_client.get_market(market_id)
        
        if not market:
            print(f"❌ [ANALYZE MARKET] Market {market_id} not found")
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Get question from market (database or contract)
        question = market.get("question") or market.get("Question") or f"Market {market_id}"
        print(f"✅ [ANALYZE MARKET] Market {market_id} found: {question[:50]}...")
        
        # Run FULL autonomous analysis (Analyzer + Trader + Judge)
        # This uses REAL APIs - no mocks
        result = await agent_service.full_analysis(
            market_question=market["question"],
            market_id=market_id
        )
        
        # Store full analysis in NeoFS if available
        if neofs_client:
            try:
                container_id = NEOFS_PUBLIC_CONTAINER_ID
                await neofs_client.upload_agent_analysis(
                    container_id=container_id,
                    market_id=market_id,
                    analysis=result
                )
            except Exception as e:
                print(f"Failed to store analysis in NeoFS: {e}")
        
        # Broadcast to WebSocket clients
        await manager.broadcast(market_id, {
            "type": "full_analysis",
            "data": result
        })
        
        return {
            "success": True,
            "analysis": result,
            "agents": {
                "analyzer": "✅ Used real APIs (PubMed, arXiv, Climate, Crypto)",
                "trader": "✅ Calculated optimal trade",
                "judge": "✅ Aggregated consensus from multiple analyses"
            },
            "note": "All data from real APIs - no mocks"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/test")
async def analyze_market_test(request: AnalyzeTestRequest):
    """
    Test endpoint for agent analysis - accepts question and oracle URL directly
    No contract market required - perfect for testing!
    
    Request body:
    {
        "question": "Will it rain in London, UK on December 25, 2024?",
        "oracle_url": "https://www.metoffice.gov.uk/weather/forecast/gcpvj0v07",
        "market_id": "test_1"  # Optional, for tracking
    }
    """
    try:
        question = request.question
        oracle_url = request.oracle_url or ""
        market_id = request.market_id or "test"
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        print(f"🧪 [TEST ANALYZE] Starting analysis for test market")
        print(f"   Question: {question}")
        print(f"   Oracle URL: {oracle_url}")
        print(f"   Market ID: {market_id}")
        
        # Run FULL autonomous analysis (Analyzer + Trader → Judge)
        # This uses REAL APIs - no mocks
        result = await agent_service.full_analysis(
            market_question=question,
            market_id=market_id
        )
        
        print(f"✅ [TEST ANALYZE] Analysis complete!")
        print(f"   Consensus Probability: {result.get('summary', {}).get('consensus_probability', 0) * 100:.1f}%")
        print(f"   Confidence: {result.get('summary', {}).get('consensus_confidence', 0) * 100:.0f}%")
        
        return {
            "success": True,
            "analysis": result,
            "test_data": {
                "question": question,
                "oracle_url": oracle_url,
                "market_id": market_id
            },
            "agents": {
                "analyzer": "✅ Used real APIs (PubMed, arXiv, Climate, Crypto)",
                "trader": "✅ Calculated optimal trade",
                "judge": "✅ Aggregated consensus from multiple analyses"
            },
            "note": "Test analysis - all data from real APIs"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [TEST ANALYZE] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/markets/{market_id}/trade/propose")
async def propose_trade(market_id: str, trade: TradeProposal):
    """
    Get trade proposal from Trader agent
    """
    try:
        # Get market data using contract client
        if not contract_client:
            raise HTTPException(status_code=503, detail="Contract client not initialized")
        
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
        if not contract_client:
            raise HTTPException(status_code=503, detail="Contract client not initialized")
        
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
        if not contract_client:
            raise HTTPException(status_code=503, detail="Contract client not initialized")
        
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

@app.post("/markets/{market_id}/resolve/demo")
async def demo_resolve_market(market_id: str, request: Request):
    """
    DEMO ONLY: Manually resolve a market for demonstration purposes
    This updates the database to show the market as resolved
    In production, markets are resolved via Oracle callbacks
    
    Body: { "outcome": "yes" | "no" }
    """
    try:
        body = await request.json()
        outcome = body.get("outcome", "").lower()
        
        # Validate outcome
        if outcome not in ["yes", "no"]:
            raise HTTPException(status_code=400, detail="Outcome must be 'yes' or 'no'")
        
        # Get market from database
        market = get_market_from_db(market_id)
        if not market:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
        
        # Update market in database
        update_market_onchain_data(market_id, {
            "is_resolved": True,
            "outcome": outcome == "yes",
            "status": "resolved"
        })
        
        print(f"✅ [DEMO RESOLVE] Market {market_id} resolved as: {outcome.upper()}")
        
        return {
            "success": True,
            "market_id": market_id,
            "outcome": outcome,
            "message": f"Market {market_id} resolved as {outcome.upper()} (DEMO MODE)"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [DEMO RESOLVE] Error: {e}")
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

@app.get("/neofs/balance")
async def get_neofs_balance():
    """
    Get NeoFS account balance
    Note: NeoFS balance is separate from Neo GAS tokens
    """
    if not neofs_client:
        raise HTTPException(status_code=503, detail="NeoFS client not configured")
    
    try:
        balance = await neofs_client.get_balance()
        return {
            "success": True,
            "balance": balance,
            "note": "NeoFS balance is separate from Neo GAS tokens. You need NeoFS balance to create containers."
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

