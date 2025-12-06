"""
Trader Agent - Proposes trade orders based on analysis
"""
import asyncio
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from spoon_ai.agents.toolcall import ToolCallAgent
    from spoon_ai.chat import ChatBot
    from spoon_ai.tools import ToolManager
    from tools import NeoRPCTool, KellyCriterionTool, ConfidenceStakeTool
except ImportError:
    print("Warning: spoon-ai-sdk not installed. Please install with: pip install spoon-ai-sdk")
    print("Using fallback implementation...")
    # Fallback for development
    ToolCallAgent = None
    ChatBot = None
    ToolManager = None


class TraderAgent:
    """
    Trader Agent that:
    1. Takes analysis results from Analyzer Agent
    2. Fetches market data from Neo blockchain
    3. Calculates optimal stake using Kelly Criterion
    4. Proposes trade orders
    """
    
    def __init__(self, llm_provider: str = None, model_name: str = None):
        # Use environment variable or default to gemini
        import os
        if llm_provider is None:
            llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
        """
        Initialize Trader Agent
        
        Args:
            llm_provider: LLM provider (openai, anthropic, gemini, etc.)
            model_name: Model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.agent = None
        
        if ToolCallAgent and ChatBot and ToolManager:
            try:
                self._initialize_agent()
            except Exception as e:
                print(f"⚠️  Warning: Failed to initialize Trader agent: {e}")
                import traceback
                traceback.print_exc()
                self.agent = None
    
    def _initialize_agent(self):
        """Initialize the SpoonOS agent"""
        # Create tools
        neo_rpc_tool = NeoRPCTool()
        kelly_tool = KellyCriterionTool()
        confidence_tool = ConfidenceStakeTool()
        
        # Create LLM
        llm = ChatBot(
            llm_provider=self.llm_provider,
            model_name=self.model_name
        )
        
        # Create agent
        self.agent = ToolCallAgent(
            llm=llm,
            available_tools=ToolManager([neo_rpc_tool, kelly_tool, confidence_tool]),
            name="trader_agent",
            description="Trader agent that proposes trades based on analysis and market data",
            system_prompt="""You are a Trader agent specialized in proposing optimal trades for prediction markets.

Your task is to:
1. Analyze the probability and confidence from the Analyzer agent
2. Fetch current market data using neo_rpc_call() to get:
   - Current odds/prices
   - Market liquidity
   - Recent trading activity
3. Calculate optimal stake using kelly_criterion_calc() or confidence_stake_calc()
4. Propose a trade order (BUY_YES or BUY_NO) with amount and confidence

Trading strategy:
- Use Kelly Criterion for optimal stake sizing when you have reliable odds
- Use confidence-based staking as a fallback
- Be conservative - don't risk more than 10% of bankroll on a single trade
- Consider market liquidity before proposing large trades
- Higher confidence in analysis = larger stake (up to limits)

Output format should be JSON with:
{
    "action": "BUY_YES" or "BUY_NO",
    "amount": 500,
    "confidence": 0.92,
    "reasoning": "Explanation of trade decision..."
}
"""
        )
    
    async def propose_trade(
        self,
        analysis: Dict[str, Any],
        market_id: Optional[str] = None,
        bankroll: float = 1000.0
    ) -> Dict[str, Any]:
        """
        Propose a trade based on analysis
        
        Args:
            analysis: Analysis result from Analyzer Agent
            market_id: Optional market ID to fetch specific market data
            bankroll: Available capital for trading
            
        Returns:
            Trade proposal dictionary
        """
        if not self.agent:
            # Fallback implementation
            return self._fallback_trade(analysis, bankroll)
        
        try:
            # Create trading prompt
            prompt = f"""Based on this analysis:
{json.dumps(analysis, indent=2)}

Please:
1. Determine if we should BUY_YES or BUY_NO based on the probability
2. Fetch current market data using neo_rpc_call() if market_id is available
3. Calculate optimal stake using kelly_criterion_calc() or confidence_stake_calc()
4. Propose a trade with action, amount, and confidence

Bankroll available: {bankroll}

Return your trade proposal in JSON format with: action, amount, confidence, and reasoning."""
            
            if market_id:
                prompt += f"\n\nMarket ID: {market_id}"
            
            # Run the agent
            response = await self.agent.run(prompt)
            
            # Parse response
            result = self._parse_agent_response(response, analysis, bankroll)
            return result
            
        except Exception as e:
            print(f"Error in trader agent: {e}")
            return self._fallback_trade(analysis, bankroll)
    
    def _parse_agent_response(
        self,
        response: str,
        analysis: Dict[str, Any],
        bankroll: float
    ) -> Dict[str, Any]:
        """
        Parse agent response to extract trade proposal
        
        Args:
            response: Agent response string
            analysis: Original analysis
            bankroll: Available bankroll
            
        Returns:
            Parsed trade proposal
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "action": result.get("action", "BUY_YES" if analysis.get("probability", 0.5) > 0.5 else "BUY_NO"),
                    "amount": float(result.get("amount", 100)),
                    "confidence": float(result.get("confidence", analysis.get("confidence", 0.5))),
                    "reasoning": result.get("reasoning", response),
                    "analysis": analysis
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract action and amount from text
        action_match = re.search(r'(BUY_YES|BUY_NO)', response, re.IGNORECASE)
        amount_match = re.search(r'amount[:\s]+([0-9.]+)', response, re.IGNORECASE)
        
        probability = analysis.get("probability", 0.5)
        action = action_match.group(1) if action_match else ("BUY_YES" if probability > 0.5 else "BUY_NO")
        amount = float(amount_match.group(1)) if amount_match else min(100.0, bankroll * 0.1)
        
        return {
            "action": action,
            "amount": amount,
            "confidence": analysis.get("confidence", 0.5),
            "reasoning": response,
            "analysis": analysis
        }
    
    def _fallback_trade(self, analysis: Dict[str, Any], bankroll: float) -> Dict[str, Any]:
        """
        Fallback trade proposal when SpoonOS is not available
        
        Args:
            analysis: Analysis result
            bankroll: Available bankroll
            
        Returns:
            Basic trade proposal
        """
        probability = analysis.get("probability", 0.5)
        confidence = analysis.get("confidence", 0.5)
        
        # Simple strategy: buy YES if probability > 0.5
        action = "BUY_YES" if probability > 0.5 else "BUY_NO"
        
        # Simple stake: 10% of bankroll scaled by confidence
        amount = min(bankroll * 0.1 * confidence, bankroll * 0.1)
        
        return {
            "action": action,
            "amount": round(amount, 2),
            "confidence": confidence,
            "reasoning": f"Fallback trade: {action} with {amount} based on probability {probability}",
            "analysis": analysis
        }


# Example usage
async def main():
    """Test the trader agent"""
    agent = TraderAgent(llm_provider="openai", model_name="gpt-4o")
    
    # Mock analysis
    analysis = {
        "probability": 0.75,
        "confidence": 0.85,
        "evidence": "Strong evidence from multiple sources",
        "sources_count": 15
    }
    
    result = await agent.propose_trade(analysis, bankroll=1000.0)
    
    print("Trade Proposal:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

