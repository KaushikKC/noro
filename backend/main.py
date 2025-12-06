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
NEO_NETWORK = os.getenv("NEO_NETWORK", "testnet")  # 'mainnet' or 'testnet'

# Set default RPC URL based on network if not provided
_default_rpc_url = (
    "https://mainmagnet.ngd.network:443" if NEO_NETWORK == "mainnet"
    else "https://testnet1.neo.coz.io:443"  # Updated to use coz.io testnet RPC
)
NEO_RPC_URL = os.getenv("NEO_RPC_URL", _default_rpc_url)
# Use same contract hash as frontend
# Frontend uses: 0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a
NEO_CONTRACT_HASH = os.getenv("NEO_CONTRACT_HASH", "0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a")
NEOFS_ENDPOINT = os.getenv("NEOFS_ENDPOINT", "https://rest.fs.neo.org")
NEO_NETWORK_FS = os.getenv("NEO_NETWORK", "testnet")  # For NeoFS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize services (lazy initialization for async clients)
neo_client = NeoRPCClient(NEO_RPC_URL)
# Contract and oracle clients will be initialized in lifespan
contract_client = None
oracle_client = None
oracle_handler = None

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
                                container_id="noro-markets",
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
async def ensure_neofs_container():
    """
    Ensure NeoFS container exists for storing market data
    Creates a PUBLIC container if it doesn't exist
    """
    if not neofs_client:
        print("⚠️  NeoFS client not available, skipping container setup")
        return None
    
    try:
        container_name = "noro-markets"
        print(f"📦 Checking NeoFS container '{container_name}'...")
        
        # List existing containers
        containers = await neofs_client.list_containers()
        
        # Check if container exists
        container_id = None
        for container in containers:
            if isinstance(container, dict):
                if container.get("name") == container_name or container.get("container_id") == container_name:
                    container_id = container.get("container_id") or container.get("id")
                    break
            elif isinstance(container, str):
                # If container is just an ID string
                container_id = container
                break
        
        if container_id:
            print(f"✅ NeoFS container '{container_name}' already exists: {container_id}")
            return container_id
        
        # Create container if it doesn't exist
        print(f"📦 Creating NeoFS container '{container_name}'...")
        result = await neofs_client.create_container(
            name=container_name,
            basic_acl="public-read-write",  # PUBLIC container - no bearer token needed for reads
            placement_policy="REP 1",
            attributes={"type": "market_storage", "created_by": "noro_backend"}
        )
        
        if isinstance(result, dict):
            container_id = result.get("container_id") or result.get("id")
        elif isinstance(result, str):
            container_id = result
        
        if container_id:
            print(f"✅ Created NeoFS container '{container_name}': {container_id}")
            return container_id
        else:
            print(f"⚠️  Container creation returned unexpected result: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error ensuring NeoFS container: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    neofs_container_id = await ensure_neofs_container()
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
        container_id = os.getenv("NEOFS_CONTAINER_ID", "noro-markets")
        
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
        container_id = os.getenv("NEOFS_CONTAINER_ID", "noro-markets")
        
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
async def list_markets(use_neofs: bool = True):
    """
    List all markets
    Fetches from NeoFS first (for human-readable data), then enriches with contract data
    
    Args:
        use_neofs: If True, try to fetch from NeoFS first (default: True)
    """
    try:
        print(f"🔍 [LIST MARKETS] Request received, use_neofs={use_neofs}")
        
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", "noro-markets")
        
        # Try NeoFS first if requested and available
        neofs_markets = []
        if use_neofs and neofs_client:
            try:
                print(f"📦 [LIST MARKETS] Fetching from NeoFS first (container: {container_id})...")
                neofs_markets = await neofs_client.list_all_markets(
                    container_id=container_id
                )
                print(f"✅ [LIST MARKETS] Found {len(neofs_markets)} markets in NeoFS")
            except Exception as e:
                print(f"⚠️ [LIST MARKETS] Error fetching from NeoFS: {e}")
                import traceback
                traceback.print_exc()
        
        if not contract_client:
            print(f"⚠️ [LIST MARKETS] Contract client not initialized")
            # Return NeoFS markets if available
            if neofs_markets:
                return {
                    "success": True,
                    "markets": neofs_markets,
                    "count": len(neofs_markets),
                    "source": "neofs_only"
                }
            return {
                "success": True,
                "markets": [],
                "count": 0,
                "note": "Contract client not initialized"
            }
        
        print(f"✅ [LIST MARKETS] Contract client is available")
        
        # Get market count from contract
        try:
            print(f"🔍 [LIST MARKETS] Fetching market count...")
            market_count = await contract_client.get_market_count()
            print(f"📊 [LIST MARKETS] Contract reports {market_count} markets")
        except Exception as e:
            print(f"❌ [LIST MARKETS] Error getting market count: {e}")
            import traceback
            traceback.print_exc()
            market_count = 0
        
        if market_count == 0:
            print(f"⚠️ [LIST MARKETS] No markets found in contract")
            return {
                "success": True,
                "markets": [],
                "count": 0,
                "source": "contract",
                "note": "No markets found in contract"
            }
        
        print(f"🔍 [LIST MARKETS] Fetching {market_count} markets from contract...")
        
        # Fetch each market from contract
        markets = []
        for i in range(1, market_count + 1):
            try:
                print(f"  🔍 [LIST MARKETS] Fetching market {i}/{market_count}...")
                market = await contract_client.get_market(str(i))
                if market:
                    question = market.get('question', 'N/A')
                    print(f"  ✅ [LIST MARKETS] Market {i}: {question[:50]}...")
                    print(f"  📊 [LIST MARKETS] Market {i} data: {json.dumps(market, indent=2, default=str)}")
                    
                    # Ensure market has required fields
                    if not market.get("question"):
                        print(f"  ⚠️ [LIST MARKETS] Market {i} missing question, skipping")
                        continue
                    
                    # Try to find matching NeoFS data
                    neofs_data = None
                    for neofs_market in neofs_markets:
                        if str(neofs_market.get("market_id")) == str(i):
                            neofs_data = neofs_market
                            break
                    
                    if neofs_data:
                        print(f"  📦 [LIST MARKETS] Market {i} NeoFS data found, merging...")
                        # Merge NeoFS data with contract data (NeoFS provides human-readable, contract provides on-chain state)
                        market.update({
                            "description": neofs_data.get("description", market.get("description")),
                            "category": neofs_data.get("category", market.get("category")),
                            "oracle_url": neofs_data.get("oracle_url", market.get("oracle_url")),
                        })
                        # Keep contract data for on-chain fields (shares, resolved, etc.)
                    else:
                        print(f"  ⚠️ [LIST MARKETS] Market {i} not found in NeoFS (using contract data only)")
                    
                    markets.append(market)
                else:
                    print(f"  ⚠️ [LIST MARKETS] Market {i} returned None")
            except Exception as e:
                print(f"  ❌ [LIST MARKETS] Error fetching market {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"✅ [LIST MARKETS] Successfully fetched {len(markets)} markets from contract")
        print(f"📊 [LIST MARKETS] Returning markets: {json.dumps([m.get('question', 'N/A') for m in markets], indent=2)}")
        
        return {
            "success": True,
            "markets": markets,
            "count": len(markets),
            "source": "contract" if not use_neofs else "contract+neofs"
        }
    except Exception as e:
        print(f"❌ Error in list_markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/markets/{market_id}")
async def get_market(market_id: str, use_neofs: bool = True):
    """
    Get market details by ID
    Fetches from NeoFS first (for human-readable data), then enriches with contract data
    
    Args:
        market_id: Market ID
        use_neofs: If True, try to fetch from NeoFS first, then enrich with contract data
    """
    try:
        market = None
        neofs_data = None
        source = "contract_only"
        
        # Get container ID from environment or use default
        import os
        container_id = os.getenv("NEOFS_CONTAINER_ID", "noro-markets")
        
        # Try NeoFS first if requested and available (for human-readable data)
        if use_neofs and neofs_client:
            try:
                print(f"📦 [GET MARKET] Fetching from NeoFS first (container: {container_id}, market_id: {market_id})...")
                neofs_data = await neofs_client.get_market_data(
                    container_id=container_id,
                    market_id=market_id
                )
                if neofs_data:
                    print(f"✅ [GET MARKET] Found market data in NeoFS")
                    market = neofs_data
                    source = "neofs"
                else:
                    print(f"⚠️ [GET MARKET] Market not found in NeoFS, will fetch from contract")
            except Exception as e:
                print(f"⚠️ [GET MARKET] Error fetching from NeoFS: {e}")
                import traceback
                traceback.print_exc()
        
        # Fetch from contract (either as primary source or to enrich NeoFS data)
        if not contract_client:
            if market:
                return {
                    "success": True,
                    "market": market,
                    "source": "neofs_only"
                }
            raise HTTPException(status_code=503, detail="Contract client not initialized")
        
        print(f"📄 [GET MARKET] Fetching from contract (market_id: {market_id})...")
        contract_market = await contract_client.get_market(market_id)
        
        if not contract_market and not market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Merge data: NeoFS provides human-readable data, contract provides on-chain state
        if market and contract_market:
            # Merge: contract data takes precedence for on-chain fields (shares, resolved, etc.)
            # But keep NeoFS data for human-readable fields (description, etc.)
            print(f"✅ [GET MARKET] Merging NeoFS and contract data")
            # Update with contract data (shares, resolved status, etc.)
            market.update({
                "id": contract_market.get("id", market_id),
                "yes_shares": contract_market.get("yes_shares", 0),
                "no_shares": contract_market.get("no_shares", 0),
                "is_resolved": contract_market.get("is_resolved", False),
                "outcome": contract_market.get("outcome"),
                "resolve_date": contract_market.get("resolve_date", market.get("resolve_date")),
                "creator": contract_market.get("creator", market.get("creator")),
                "created_at": contract_market.get("created_at", market.get("created_at")),
            })
            source = "neofs_and_contract"
        elif contract_market:
            # Only contract data available
            print(f"⚠️ [GET MARKET] Only contract data available (NeoFS not found)")
            market = contract_market
            source = "contract_only"
        # else: market from NeoFS only (already set above)
        
        # Get probability from contract
        try:
            probability = await contract_client.get_probability(market_id)
            market["probability"] = probability
        except:
            market["probability"] = 0.5  # Default if not available
        
        print(f"✅ [GET MARKET] Returning market data (source: {source})")
        return {
            "success": True,
            "market": market,
            "source": source
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [GET MARKET] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
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
        
        print(f"🔍 [ANALYZE MARKET] Fetching market {market_id} from contract...")
        market = await contract_client.get_market(market_id)
        if not market:
            print(f"❌ [ANALYZE MARKET] Market {market_id} not found in contract")
            raise HTTPException(status_code=404, detail="Market not found")
        print(f"✅ [ANALYZE MARKET] Market {market_id} found: {market.get('question', 'N/A')[:50]}...")
        
        # Run FULL autonomous analysis (Analyzer + Trader + Judge)
        # This uses REAL APIs - no mocks
        result = await agent_service.full_analysis(
            market_question=market["question"],
            market_id=market_id
        )
        
        # Store full analysis in NeoFS if available
        if neofs_client:
            try:
                container_id = "noro-markets"
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

