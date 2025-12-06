"""
Main Orchestrator - Coordinates Analyzer and Trader agents
"""
import asyncio
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from analyzer_agent import AnalyzerAgent
from trader_agent import TraderAgent
from judge_agent import JudgeAgent

# Load environment variables
load_dotenv()


class NoroOrchestrator:
    """
    Main orchestrator that coordinates the Analyzer and Trader agents
    """
    
    def __init__(
        self,
        llm_provider: str = None,
        model_name: str = None
    ):
        # Use environment variable or default to gemini
        import os
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Load .env from agents directory (in case we're imported from backend)
        agents_dir = Path(__file__).parent
        env_file = agents_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
        else:
            # Fallback to current directory .env
            load_dotenv()
        
        if llm_provider is None:
            llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
        
        # Debug: Print what provider we're using
        api_key_set = bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        print(f"🔧 Orchestrator init: provider={llm_provider}, model={model_name}, API key={'SET' if api_key_set else 'NOT SET'}")
        """
        Initialize orchestrator with agents
        
        Args:
            llm_provider: LLM provider to use
            model_name: Model name to use
        """
        self.analyzer = AnalyzerAgent(llm_provider=llm_provider, model_name=model_name)
        self.trader = TraderAgent(llm_provider=llm_provider, model_name=model_name)
        self.judge = JudgeAgent(llm_provider=llm_provider, model_name=model_name)
    
    async def process_market(
        self,
        market_question: str,
        market_id: Optional[str] = None,
        bankroll: float = 1000.0,
        max_papers: int = 10
    ) -> Dict[str, Any]:
        """
        Process a prediction market question through the full pipeline
        
        Args:
            market_question: The prediction market question
            market_id: Optional Neo blockchain market ID
            bankroll: Available capital for trading
            max_papers: Maximum papers to fetch per source
            
        Returns:
            Complete result with analysis and trade proposal
        """
        print(f"🔍 Analyzing market: {market_question}")
        
        # Step 1: Analyze the question
        print("📊 Running Analyzer Agent...")
        analysis = await self.analyzer.analyze(market_question, max_papers=max_papers)
        
        print(f"✅ Analysis complete:")
        print(f"   Probability: {analysis.get('probability', 0):.2%}")
        print(f"   Confidence: {analysis.get('confidence', 0):.2%}")
        print(f"   Sources: {analysis.get('sources_count', 0)}")
        
        # Step 2: Propose trade
        print("\n💰 Running Trader Agent...")
        # Add longer delay to avoid rate limits (Gemini free tier is strict)
        import asyncio
        await asyncio.sleep(5)  # 5 second delay for Gemini free tier
        try:
            trade_proposal = await self.trader.propose_trade(
                analysis,
                market_id=market_id,
                bankroll=bankroll
            )
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                print(f"   ⚠️  Trader agent hit rate limit: {e}")
                print(f"   💡 Using fallback trade based on first analysis")
            else:
                print(f"   ⚠️  Trader agent error: {e}")
            # Fallback trade proposal
            trade_proposal = {
                "action": "BUY_YES" if analysis.get("probability", 0.5) > 0.5 else "BUY_NO",
                "amount": min(bankroll * 0.1 * analysis.get("confidence", 0.5), bankroll * 0.1),
                "confidence": analysis.get("confidence", 0.5),
                "reasoning": f"Fallback trade based on analysis probability {analysis.get('probability', 0.5):.2%}"
            }
        
        print(f"✅ Trade proposal complete:")
        print(f"   Action: {trade_proposal.get('action', 'N/A')}")
        print(f"   Amount: {trade_proposal.get('amount', 0):.2f}")
        print(f"   Confidence: {trade_proposal.get('confidence', 0):.2%}")
        
        # Step 3: Judge Agent - Run multiple analyses and aggregate
        print("\n⚖️  Running Judge Agent (multiple analyses)...")
        
        # Run multiple analyses for consensus (simulate multiple analyzer runs)
        analyses = [analysis]  # Start with first analysis
        
        # For Gemini free tier, reduce to 1 additional analysis (total 2 instead of 3)
        # This reduces API calls and rate limit issues
        additional_analyses_count = 1  # Reduced from 2 to 1 for rate limit management
        
        # Run additional analyses for consensus (with longer delays to avoid rate limits)
        import asyncio
        for i in range(additional_analyses_count):
            print(f"   Running analysis {i+2}/{additional_analyses_count + 1}...")
            # Add longer delay to avoid rate limits (Gemini free tier is strict)
            await asyncio.sleep(10)  # 10 second delay between calls for Gemini free tier
            try:
                additional_analysis = await self.analyzer.analyze(market_question, max_papers=max_papers)
                analyses.append(additional_analysis)
                print(f"   ✅ Analysis {i+2} completed successfully")
            except Exception as e:
                error_str = str(e).lower()
                if "rate limit" in error_str or "quota" in error_str:
                    print(f"   ⚠️  Analysis {i+2} hit rate limit: {e}")
                    print(f"   💡 Using first analysis as fallback")
                else:
                    print(f"   ⚠️  Analysis {i+2} failed: {e}")
                # Use first analysis as fallback if subsequent ones fail
                analyses.append(analysis)
        
        # Judge aggregates all analyses (with longer delay)
        await asyncio.sleep(5)  # 5 second delay before judge
        try:
            judgment = await self.judge.aggregate(analyses, market_question)
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                print(f"   ⚠️  Judge agent hit rate limit: {e}")
                print(f"   💡 Using weighted average fallback")
            else:
                print(f"   ⚠️  Judge agent error: {e}")
            # Fallback judgment using weighted average of available analyses
            probabilities = [a.get("probability", 0.5) for a in analyses]
            confidences = [a.get("confidence", 0.5) for a in analyses]
            weighted_prob = sum(p * c for p, c in zip(probabilities, confidences)) / sum(confidences) if confidences else 0.5
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            judgment = {
                "consensus_probability": weighted_prob,
                "consensus_confidence": avg_confidence,
                "agent_count": len(analyses),
                "agreement_level": "single" if len(analyses) == 1 else "medium",
                "reasoning": f"Using weighted average of {len(analyses)} analyses due to rate limits",
                "weighted_average": weighted_prob,
                "confidence_weighted_avg": avg_confidence
            }
        
        print(f"✅ Consensus judgment complete:")
        print(f"   Consensus Probability: {judgment.get('consensus_probability', 0):.2%}")
        print(f"   Consensus Confidence: {judgment.get('consensus_confidence', 0):.2%}")
        print(f"   Agreement Level: {judgment.get('agreement_level', 'N/A')}")
        print(f"   Analyses Count: {judgment.get('agent_count', 0)}")
        
        # Combine results with judgment
        result = {
            "market_question": market_question,
            "market_id": market_id,
            "analyses": analyses,  # All individual analyses
            "judgment": judgment,  # Consensus judgment
            "trade_proposal": trade_proposal,
            "summary": {
                "consensus_probability": judgment.get("consensus_probability", 0),
                "consensus_confidence": judgment.get("consensus_confidence", 0),
                "recommended_action": trade_proposal.get("action"),
                "recommended_stake": trade_proposal.get("amount", 0),
                "agreement_level": judgment.get("agreement_level", "medium"),
                "analyses_count": judgment.get("agent_count", 1)
            }
        }
        
        return result
    
    async def batch_process(
        self,
        market_questions: list[str],
        bankroll: float = 1000.0
    ) -> list[Dict[str, Any]]:
        """
        Process multiple market questions
        
        Args:
            market_questions: List of market questions
            bankroll: Available capital (split across markets)
            
        Returns:
            List of results
        """
        results = []
        per_market_bankroll = bankroll / len(market_questions) if market_questions else bankroll
        
        for question in market_questions:
            result = await self.process_market(
                market_question=question,
                bankroll=per_market_bankroll
            )
            results.append(result)
            print("\n" + "="*50 + "\n")
        
        return results


# Example usage
async def main():
    """Test the orchestrator"""
    orchestrator = NoroOrchestrator()  # Uses DEFAULT_LLM_PROVIDER from .env
    
    # Example market question
    market_question = "Will a new cancer treatment be approved by FDA in 2025?"
    
    result = await orchestrator.process_market(
        market_question=market_question,
        bankroll=1000.0
    )
    
    print("\n" + "="*50)
    print("FINAL RESULT")
    print("="*50)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

