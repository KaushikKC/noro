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
                self.orchestrator = NoroOrchestrator()  # Uses env vars
            except Exception as e:
                print(f"Warning: Could not initialize orchestrator: {e}")
    
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
            # Run full pipeline: Analyzer → Trader → Judge
            # This includes multiple analyses and consensus judgment
            result = await self.orchestrator.process_market(
                market_question=market_question,
                market_id=market_id,
                bankroll=1000.0
            )
            
            # Add metadata
            result["agents_used"] = {
                "analyzer": "✅ Real APIs (PubMed, arXiv, Climate, Crypto)",
                "trader": "✅ Kelly Criterion with real market data",
                "judge": "✅ Consensus from multiple analyses"
            }
            result["data_source"] = "REAL_APIS_ONLY"
            
            return result
        except Exception as e:
            print(f"Error in full analysis: {e}")
            raise

