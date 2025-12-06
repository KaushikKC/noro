"""
Judge Agent - Aggregates results from multiple agents and makes consensus decisions
Uses SpoonOS ToolCallAgent for intelligent aggregation
"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from spoon_ai.agents.toolcall import ToolCallAgent
    from spoon_ai.chat import ChatBot
    from spoon_ai.tools import ToolManager
except ImportError:
    print("Warning: spoon-ai-sdk not installed. Please install with: pip install spoon-ai-sdk")
    print("Using fallback implementation...")
    ToolCallAgent = None
    ChatBot = None
    ToolManager = None


class JudgeAgent:
    """
    Judge Agent that:
    1. Takes multiple analysis results (from Analyzer agents)
    2. Aggregates probabilities using weighted consensus
    3. Makes final judgment on market outcome
    4. Provides confidence in the consensus
    """
    
    def __init__(self, llm_provider: str = None, model_name: str = None):
        # Use environment variable or default to gemini
        import os
        if llm_provider is None:
            llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")  # Using DeepSeek (paid account)
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "deepseek-chat")  # DeepSeek model
        """
        Initialize Judge Agent
        
        Args:
            llm_provider: LLM provider (openai, anthropic, gemini, etc.)
            model_name: Model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.agent = None
        
        if ToolCallAgent and ChatBot and ToolManager:
            self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the SpoonOS agent"""
        # Create LLM
        # Set max_tokens for DeepSeek (valid range: 1-8192)
        import os
        max_tokens = None
        if self.llm_provider == "deepseek":
            max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "8192"))  # Default to 8192 for DeepSeek
        
        llm = ChatBot(
            llm_provider=self.llm_provider,
            model_name=self.model_name,
            max_tokens=max_tokens if max_tokens else None
        )
        
        # Judge agent doesn't need external tools - it analyzes analyses
        self.agent = ToolCallAgent(
            llm=llm,
            available_tools=ToolManager([]),  # No external tools needed
            name="judge_agent",
            description="Judge agent that aggregates multiple analyses and makes consensus decisions",
            system_prompt="""You are a Judge agent specialized in aggregating multiple analyses and making consensus decisions.

Your task is to:
1. Review multiple analysis results from different Analyzer agents
2. Consider the confidence and evidence quality of each analysis
3. Calculate a weighted consensus probability
4. Determine overall confidence in the consensus
5. Provide reasoning for your judgment

Aggregation strategy:
- Weight analyses by their confidence scores
- Consider the number and quality of sources in each analysis
- Look for agreement or disagreement between analyses
- Higher confidence analyses should have more weight
- If analyses disagree significantly, lower overall confidence

Output format should be JSON with:
{
    "consensus_probability": 0.75,
    "consensus_confidence": 0.85,
    "agent_count": 3,
    "agreement_level": "high" or "medium" or "low",
    "reasoning": "Explanation of consensus calculation...",
    "weighted_average": 0.75,
    "confidence_weighted_avg": 0.82
}
"""
        )
    
    async def aggregate(
        self,
        analyses: List[Dict[str, Any]],
        market_question: str
    ) -> Dict[str, Any]:
        """
        Aggregate multiple analyses into a consensus judgment
        
        Args:
            analyses: List of analysis results from Analyzer agents
            market_question: The market question being judged
            
        Returns:
            Consensus judgment with probability, confidence, etc.
        """
        if not analyses:
            return {
                "consensus_probability": 0.5,
                "consensus_confidence": 0.0,
                "agent_count": 0,
                "agreement_level": "none",
                "reasoning": "No analyses provided",
                "error": "No analyses to aggregate"
            }
        
        if not self.agent:
            # Fallback: simple weighted average
            return self._fallback_aggregate(analyses)
        
        try:
            # Reset agent state before running (fixes "not in IDLE state" error)
            if hasattr(self.agent, 'clear'):
                self.agent.clear()
            elif hasattr(self.agent, 'reset'):
                self.agent.reset()
            
            # Prepare prompt with all analyses
            analyses_json = json.dumps(analyses, indent=2)
            
            prompt = f"""You are judging a prediction market question:

"{market_question}"

You have received {len(analyses)} analysis results:

{analyses_json}

Please:
1. Review each analysis's probability and confidence
2. Calculate a weighted consensus probability (weight by confidence)
3. Determine overall confidence in the consensus
4. Assess agreement level between analyses
5. Provide reasoning for your judgment

Return your judgment in JSON format with: consensus_probability, consensus_confidence, agent_count, agreement_level, reasoning, weighted_average, confidence_weighted_avg."""
            
            # Run the agent
            response = await self.agent.run(prompt)
            
            # Parse response
            result = self._parse_agent_response(response, analyses, market_question)
            return result
            
        except Exception as e:
            print(f"Error in judge agent: {e}")
            return self._fallback_aggregate(analyses)
    
    def _parse_agent_response(
        self,
        response: str,
        analyses: List[Dict[str, Any]],
        market_question: str
    ) -> Dict[str, Any]:
        """
        Parse agent response to extract consensus judgment
        
        Args:
            response: Agent response string
            analyses: Original analyses
            market_question: Market question
            
        Returns:
            Parsed consensus judgment
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*"consensus_probability"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "consensus_probability": float(result.get("consensus_probability", 0.5)),
                    "consensus_confidence": float(result.get("consensus_confidence", 0.5)),
                    "agent_count": len(analyses),
                    "agreement_level": result.get("agreement_level", "medium"),
                    "reasoning": result.get("reasoning", response),
                    "weighted_average": float(result.get("weighted_average", 0.5)),
                    "confidence_weighted_avg": float(result.get("confidence_weighted_avg", 0.5)),
                    "market_question": market_question
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract numbers from text
        prob_match = re.search(r'consensus_probability[:\s]+([0-9.]+)', response, re.IGNORECASE)
        conf_match = re.search(r'consensus_confidence[:\s]+([0-9.]+)', response, re.IGNORECASE)
        
        consensus_prob = float(prob_match.group(1)) if prob_match else 0.5
        consensus_conf = float(conf_match.group(1)) if conf_match else 0.5
        
        return {
            "consensus_probability": consensus_prob,
            "consensus_confidence": consensus_conf,
            "agent_count": len(analyses),
            "agreement_level": "medium",
            "reasoning": response,
            "weighted_average": consensus_prob,
            "confidence_weighted_avg": consensus_conf,
            "market_question": market_question
        }
    
    def _fallback_aggregate(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback aggregation using simple weighted average
        
        Args:
            analyses: List of analyses
            
        Returns:
            Consensus judgment
        """
        if not analyses:
            return {
                "consensus_probability": 0.5,
                "consensus_confidence": 0.0,
                "agent_count": 0,
                "agreement_level": "none",
                "reasoning": "No analyses provided"
            }
        
        # Calculate weighted average by confidence
        total_weight = 0
        weighted_sum = 0
        confidences = []
        probabilities = []
        
        for analysis in analyses:
            prob = analysis.get("probability", 0.5)
            conf = analysis.get("confidence", 0.5)
            
            probabilities.append(prob)
            confidences.append(conf)
            
            weight = conf
            weighted_sum += prob * weight
            total_weight += weight
        
        # Weighted average probability
        weighted_avg = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Agreement level (standard deviation of probabilities)
        import statistics
        if len(probabilities) > 1:
            std_dev = statistics.stdev(probabilities)
            if std_dev < 0.1:
                agreement = "high"
            elif std_dev < 0.2:
                agreement = "medium"
            else:
                agreement = "low"
        else:
            agreement = "single"
        
        return {
            "consensus_probability": round(weighted_avg, 4),
            "consensus_confidence": round(avg_confidence, 4),
            "agent_count": len(analyses),
            "agreement_level": agreement,
            "reasoning": f"Fallback weighted average of {len(analyses)} analyses. Agreement: {agreement}.",
            "weighted_average": round(weighted_avg, 4),
            "confidence_weighted_avg": round(avg_confidence, 4)
        }


# Example usage
async def main():
    """Test the judge agent"""
    agent = JudgeAgent(llm_provider="openai", model_name="gpt-4o")
    
    # Mock multiple analyses
    analyses = [
        {
            "probability": 0.75,
            "confidence": 0.85,
            "evidence": "Strong evidence from 15 sources",
            "sources_count": 15
        },
        {
            "probability": 0.70,
            "confidence": 0.80,
            "evidence": "Moderate evidence from 10 sources",
            "sources_count": 10
        },
        {
            "probability": 0.80,
            "confidence": 0.90,
            "evidence": "Very strong evidence from 20 sources",
            "sources_count": 20
        }
    ]
    
    result = await agent.aggregate(
        analyses=analyses,
        market_question="Will a new cancer treatment be approved by FDA in 2025?"
    )
    
    print("Consensus Judgment:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

