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
            llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")  # Using DeepSeek (paid account)
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "deepseek-chat")  # DeepSeek model
        
        # Debug: Print what provider we're using
        api_key_set = bool(
            os.getenv("DEEPSEEK_API_KEY") or
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("ANTHROPIC_API_KEY") or
            os.getenv("OPENROUTER_API_KEY")
        )
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
        
        # Step 2: Propose trade (using fallback to reduce API calls)
        print("\n💰 Generating Trade Proposal...")
        print("   ℹ️  Using fallback trade calculation (no API call) to reduce requests")
        # Use fallback trade proposal to avoid API call
        # This reduces total API requests significantly
        trade_proposal = {
            "action": "BUY_YES" if analysis.get("probability", 0.5) > 0.5 else "BUY_NO",
            "amount": min(bankroll * 0.1 * analysis.get("confidence", 0.5), bankroll * 0.1),
            "confidence": analysis.get("confidence", 0.5),
            "reasoning": f"Trade based on analysis probability {analysis.get('probability', 0.5):.2%} and confidence {analysis.get('confidence', 0.5):.2%}"
        }
        
        print(f"✅ Trade proposal complete:")
        print(f"   Action: {trade_proposal.get('action', 'N/A')}")
        print(f"   Amount: {trade_proposal.get('amount', 0):.2f}")
        print(f"   Confidence: {trade_proposal.get('confidence', 0):.2%}")
        
        # Step 3: Generate Consensus Judgment (using fallback to reduce API calls)
        print("\n⚖️  Generating Consensus Judgment...")
        print("   ℹ️  Using fallback weighted average (no API call) to reduce requests")
        # Small delay for DeepSeek (paid account has better limits, but still good practice)
        import asyncio
        await asyncio.sleep(1)  # 1 second delay
        
        # Use only the first analysis
        analyses = [analysis]
        
        # Use fallback judgment to avoid API call
        # This reduces total API requests significantly
        probabilities = [a.get("probability", 0.5) for a in analyses]
        confidences = [a.get("confidence", 0.5) for a in analyses]
        weighted_prob = sum(p * c for p, c in zip(probabilities, confidences)) / sum(confidences) if confidences else 0.5
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        judgment = {
            "consensus_probability": weighted_prob,
            "consensus_confidence": avg_confidence,
            "agent_count": len(analyses),
            "agreement_level": "single",
            "reasoning": f"Consensus based on single analysis with probability {weighted_prob:.2%} and confidence {avg_confidence:.2%}",
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

