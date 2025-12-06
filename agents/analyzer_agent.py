"""
Analyzer Agent - Fetches data from PubMed/arXiv and generates probability predictions
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
    from tools import PubMedTool, ArxivTool, ClimateDataTool, CryptoTool
except ImportError:
    print("Warning: spoon-ai-sdk not installed. Please install with: pip install spoon-ai-sdk")
    print("Using fallback implementation...")
    # Fallback for development
    ToolCallAgent = None
    ChatBot = None
    ToolManager = None


class AnalyzerAgent:
    """
    Analyzer Agent that:
    1. Fetches scientific papers from PubMed and arXiv
    2. Analyzes the evidence
    3. Generates probability predictions with confidence scores
    """
    
    def __init__(self, llm_provider: str = None, model_name: str = None):
        # Use environment variable or default to gemini
        import os
        if llm_provider is None:
            llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
        if model_name is None:
            model_name = os.getenv("DEFAULT_MODEL", "gemini-2.0-flash-exp")
        """
        Initialize Analyzer Agent
        
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
        # Create tools - ALL REAL APIs, NO MOCKS
        pubmed_tool = PubMedTool()
        arxiv_tool = ArxivTool()
        climate_tool = ClimateDataTool()
        crypto_tool = CryptoTool()
        
        # Create LLM
        llm = ChatBot(
            llm_provider=self.llm_provider,
            model_name=self.model_name
        )
        
        # Create agent with all real data tools
        self.agent = ToolCallAgent(
            llm=llm,
            available_tools=ToolManager([pubmed_tool, arxiv_tool, climate_tool, crypto_tool]),
            name="analyzer_agent",
            description="Analyzer agent that analyzes scientific papers and generates probability predictions",
            system_prompt="""You are an Analyzer agent specialized in analyzing scientific evidence.

Your task is to:
1. Search PubMed and arXiv for relevant scientific papers related to a prediction market question
2. Analyze the evidence from these papers
3. Calculate a probability (0-1) that the outcome will occur
4. Provide confidence score (0-1) for your analysis
5. Summarize key evidence that supports your probability estimate

When analyzing:
- Consider the recency and quality of sources
- Look for consensus or disagreement in the literature
- Consider sample sizes and study quality
- Be conservative with probabilities if evidence is limited
- Always provide reasoning for your probability estimate

Output format should be JSON with:
{
    "probability": 0.75,
    "confidence": 0.85,
    "evidence": "Summary of key findings...",
    "sources_count": 10
}
"""
        )
    
    async def analyze(self, market_question: str, max_papers: int = 10) -> Dict[str, Any]:
        """
        Analyze a market question and return probability prediction
        
        Args:
            market_question: The prediction market question to analyze
            max_papers: Maximum number of papers to fetch from each source
            
        Returns:
            Dictionary with probability, confidence, evidence, etc.
        """
        if not self.agent:
            # Fallback implementation
            return self._fallback_analyze(market_question)
        
        try:
            # Create analysis prompt
            prompt = f"""Analyze the following prediction market question:

"{market_question}"

Please:
1. Use appropriate tools based on the question type:
   - For scientific questions: Use pubmed_search() and arxiv_search()
   - For weather/climate questions: Use climate_data() to get real weather data
   - For crypto questions: Use crypto_data() to get real price data
2. Analyze the REAL data from these sources (NO MOCK DATA)
3. Calculate a probability (0-1) that the outcome will occur based on REAL evidence
4. Provide your confidence (0-1) in this analysis
5. Summarize the key evidence from REAL sources

IMPORTANT: Only use real APIs. Never use mock or placeholder data.

Return your analysis in JSON format with: probability, confidence, evidence, and sources_count."""
            
            # Run the agent
            response = await self.agent.run(prompt)
            
            # Parse response to extract JSON
            result = self._parse_agent_response(response, market_question)
            return result
            
        except Exception as e:
            print(f"Error in analyzer agent: {e}")
            return self._fallback_analyze(market_question)
    
    def _parse_agent_response(self, response: str, market_question: str) -> Dict[str, Any]:
        """
        Parse agent response to extract structured data
        
        Args:
            response: Agent response string
            market_question: Original market question
            
        Returns:
            Parsed result dictionary
        """
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*"probability"[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "probability": float(result.get("probability", 0.5)),
                    "confidence": float(result.get("confidence", 0.5)),
                    "evidence": result.get("evidence", response),
                    "sources_count": int(result.get("sources_count", 0)),
                    "market_question": market_question
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract numbers from text
        prob_match = re.search(r'probability[:\s]+([0-9.]+)', response, re.IGNORECASE)
        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', response, re.IGNORECASE)
        
        probability = float(prob_match.group(1)) if prob_match else 0.5
        confidence = float(conf_match.group(1)) if conf_match else 0.5
        
        return {
            "probability": probability,
            "confidence": confidence,
            "evidence": response,
            "sources_count": 0,
            "market_question": market_question
        }
    
    def _fallback_analyze(self, market_question: str) -> Dict[str, Any]:
        """
        Fallback analysis when SpoonOS is not available
        
        Args:
            market_question: Market question to analyze
            
        Returns:
            Basic analysis result
        """
        return {
            "probability": 0.5,
            "confidence": 0.3,
            "evidence": f"Fallback analysis for: {market_question}. Install spoon-ai-sdk for full functionality.",
            "sources_count": 0,
            "market_question": market_question
        }


# Example usage
async def main():
    """Test the analyzer agent"""
    agent = AnalyzerAgent(llm_provider="openai", model_name="gpt-4o")
    
    result = await agent.analyze(
        "Will a new cancer treatment be approved by FDA in 2025?"
    )
    
    print("Analysis Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

