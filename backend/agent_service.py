"""
Agent Service - Wraps SpoonOS agents for backend use
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add agents directory to path
agents_path = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(agents_path))

# Load agents .env file if it exists (MUST be done before importing orchestrator)
agents_env_file = agents_path / ".env"
if agents_env_file.exists():
    from dotenv import load_dotenv
    # Load agents .env file - this ensures API keys are available
    load_dotenv(agents_env_file, override=True)  # override=True to use agents' .env values
    print(f"✅ Loaded agents .env file from: {agents_env_file}")
    
    # Verify API keys are loaded
    import os
    gemini_key = os.getenv("GEMINI_API_KEY")
    default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    print(f"   DEFAULT_LLM_PROVIDER: {default_provider}")
    print(f"   GEMINI_API_KEY: {'SET' if gemini_key else 'NOT SET'}")
else:
    print(f"⚠️  Warning: agents .env file not found at: {agents_env_file}")
    print(f"   Agents will not be able to initialize without API keys!")

try:
    from orchestrator import NoroOrchestrator
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    print("Warning: Agents not available. Install spoon-ai-sdk in agents/venv")


class AgentService:
    """Service for running SpoonOS agents"""
    
    def __init__(self):
        self.orchestrator = None
        if AGENTS_AVAILABLE:
            try:
                # Initialize orchestrator - uses DEFAULT_LLM_PROVIDER from .env
                # Will use gemini if GEMINI_API_KEY is set
                print("🔧 Initializing orchestrator...")
                self.orchestrator = NoroOrchestrator()  # Uses env vars
                print("✅ Orchestrator initialized successfully")
                
                # Check if agents are actually initialized
                analyzer_ready = hasattr(self.orchestrator, 'analyzer') and self.orchestrator.analyzer.agent is not None
                trader_ready = hasattr(self.orchestrator, 'trader') and self.orchestrator.trader.agent is not None
                judge_ready = hasattr(self.orchestrator, 'judge') and self.orchestrator.judge.agent is not None
                
                print(f"   Analyzer agent: {'✅ Initialized' if analyzer_ready else '❌ NOT initialized (will use fallback)'}")
                print(f"   Trader agent: {'✅ Initialized' if trader_ready else '❌ NOT initialized (will use fallback)'}")
                print(f"   Judge agent: {'✅ Initialized' if judge_ready else '❌ NOT initialized (will use fallback)'}")
                
                if not analyzer_ready or not trader_ready or not judge_ready:
                    print("⚠️  WARNING: Some agents are not initialized!")
                    print("   This usually means:")
                    print("   1. spoon-ai-sdk is not installed in backend environment")
                    print("   2. API keys are not set in agents/.env")
                    print("   3. LLM provider configuration is incorrect")
                    print("   Agents will use fallback responses.")
            except Exception as e:
                print(f"❌ ERROR: Could not initialize orchestrator: {e}")
                import traceback
                traceback.print_exc()
    
    async def analyze_market(self, market_question: str) -> Dict[str, Any]:
        """
        Run analyzer agent on a market question
        
        Args:
            market_question: The market question to analyze
            
        Returns:
            Analysis result with probability, confidence, evidence
        """
        if not self.orchestrator:
            # Return fallback analysis
            return {
                "probability": 0.5,
                "confidence": 0.3,
                "evidence": "Agents not available. Install spoon-ai-sdk.",
                "sources_count": 0,
                "market_question": market_question
            }
        
        try:
            analysis = await self.orchestrator.analyzer.analyze(market_question)
            return analysis
        except Exception as e:
            print(f"Error in agent analysis: {e}")
            return {
                "probability": 0.5,
                "confidence": 0.3,
                "evidence": f"Error: {str(e)}",
                "sources_count": 0,
                "market_question": market_question
            }
    
    async def propose_trade(
        self,
        market_id: str,
        market_question: str,
        analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run trader agent to propose a trade
        
        Args:
            market_id: Market ID
            market_question: Market question
            analysis: Optional pre-computed analysis
            
        Returns:
            Trade proposal with action, amount, confidence
        """
        if not self.orchestrator:
            # Return fallback trade
            return {
                "action": "BUY_YES",
                "amount": 100.0,
                "confidence": 0.3,
                "reasoning": "Agents not available. Install spoon-ai-sdk.",
                "analysis": analysis or {}
            }
        
        try:
            # If no analysis provided, run analysis first
            if not analysis:
                analysis = await self.analyze_market(market_question)
            
            # Propose trade
            trade_proposal = await self.orchestrator.trader.propose_trade(
                analysis=analysis,
                market_id=market_id,
                bankroll=1000.0  # Default bankroll
            )
            
            return trade_proposal
        except Exception as e:
            print(f"Error in trade proposal: {e}")
            return {
                "action": "BUY_YES",
                "amount": 100.0,
                "confidence": 0.3,
                "reasoning": f"Error: {str(e)}",
                "analysis": analysis or {}
            }
    
    async def full_analysis(self, market_question: str, market_id: str = None) -> Dict[str, Any]:
        """
        Run FULL autonomous analysis pipeline (Analyzer + Trader + Judge)
        Uses REAL APIs only - NO MOCK DATA
        
        Args:
            market_question: Market question
            market_id: Optional market ID
            
        Returns:
            Complete result with analyses, judgment, and trade proposal
        """
        if not self.orchestrator:
            return {
                "market_question": market_question,
                "market_id": market_id,
                "error": "Orchestrator not available. Install spoon-ai-sdk.",
                "analyses": [],
                "judgment": {
                    "consensus_probability": 0.5,
                    "consensus_confidence": 0.0
                },
                "trade_proposal": {
                    "action": "BUY_YES",
                    "amount": 100.0,
                    "confidence": 0.3
                }
            }
        
        try:
            # Check if agents are actually initialized before running
            analyzer_ready = hasattr(self.orchestrator, 'analyzer') and self.orchestrator.analyzer.agent is not None
            trader_ready = hasattr(self.orchestrator, 'trader') and self.orchestrator.trader.agent is not None
            judge_ready = hasattr(self.orchestrator, 'judge') and self.orchestrator.judge.agent is not None
            
            if not analyzer_ready or not trader_ready or not judge_ready:
                print(f"⚠️  WARNING: Agents not fully initialized!")
                print(f"   Analyzer: {'✅' if analyzer_ready else '❌'}")
                print(f"   Trader: {'✅' if trader_ready else '❌'}")
                print(f"   Judge: {'✅' if judge_ready else '❌'}")
                print(f"   This usually means spoon-ai-sdk is not installed or API keys are missing.")
                print(f"   Will use fallback responses.")
            
            # Run full pipeline: Analyzer → Trader → Judge
            # This includes multiple analyses and consensus judgment
            print(f"🔍 Starting full analysis pipeline for: {market_question[:50]}...")
            result = await self.orchestrator.process_market(
                market_question=market_question,
                market_id=market_id,
                bankroll=1000.0
            )
            
            # Check if result contains fallback indicators
            judgment = result.get("judgment", {})
            reasoning = judgment.get("reasoning", "")
            if "Fallback" in reasoning or "fallback" in reasoning.lower():
                print(f"⚠️  WARNING: Analysis used fallback logic!")
                print(f"   Reasoning: {reasoning}")
            
            # Add metadata
            result["agents_used"] = {
                "analyzer": "✅ Real APIs (PubMed, arXiv, Climate, Crypto)" if analyzer_ready else "❌ Fallback (agent not initialized)",
                "trader": "✅ Kelly Criterion with real market data" if trader_ready else "❌ Fallback (agent not initialized)",
                "judge": "✅ Consensus from multiple analyses" if judge_ready else "❌ Fallback (agent not initialized)"
            }
            result["data_source"] = "REAL_APIS_ONLY" if (analyzer_ready and trader_ready and judge_ready) else "FALLBACK_MODE"
            
            return result
        except Exception as e:
            print(f"❌ ERROR in full analysis: {e}")
            import traceback
            traceback.print_exc()
            raise

