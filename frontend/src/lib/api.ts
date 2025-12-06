/**
 * noro API Client
 * Fetches market data from backend API (which uses NeoFS for storage)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Market {
  id: string;
  question: string;
  description?: string;
  category: string;
  resolve_date?: string;
  resolveDate?: string;
  probability?: number;
  volume?: string;
  yes_shares?: number;
  no_shares?: number;
  is_resolved?: boolean;
  isResolved?: boolean;
  outcome?: "Yes" | "No" | boolean;
  creator?: string;
  created_at?: string;
  oracle_url?: string;
}

export interface MarketCreateRequest {
  question: string;
  description: string;
  category: string;
  resolve_date: string;
  oracle_url: string;
  initial_liquidity: number;
}

/**
 * Fetch all markets from backend API
 * Backend will fetch from NeoFS first, then enrich with contract data
 */
export async function fetchMarkets(
  useNeoFS: boolean = true
): Promise<Market[]> {
  try {
    const response = await fetch(`${API_BASE}/markets?use_neofs=${useNeoFS}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch markets: ${response.statusText}`);
    }

    const data = await response.json();
    if (data.success && data.markets) {
      // Normalize market data format
      return data.markets.map((m: Record<string, unknown>) => ({
        id: m.id || m.market_id || String(m.Id || ""),
        question: m.question || m.Question || "",
        description: m.description || m.Description || "",
        category: m.category || m.Category || "Others",
        resolveDate: String(
          m.resolve_date || m.resolveDate || m.ResolveDate || ""
        ),
        probability: typeof m.probability === "number" ? m.probability : 50,
        volume:
          (typeof m.volume === "string" ? m.volume : undefined) ||
          formatVolume(
            typeof m.yes_shares === "number"
              ? m.yes_shares
              : typeof m.YesShares === "number"
              ? m.YesShares
              : 0,
            typeof m.no_shares === "number"
              ? m.no_shares
              : typeof m.NoShares === "number"
              ? m.NoShares
              : 0
          ),
        isResolved: Boolean(m.is_resolved || m.isResolved || m.Resolved),
        outcome: m.outcome || m.Outcome,
        creator: m.creator || m.Creator,
        created_at: m.created_at || m.createdAt || m.CreatedAt,
        oracle_url: m.oracle_url || m.oracleUrl || m.OracleUrl,
      }));
    }
    return [];
  } catch (error) {
    console.error("Error fetching markets:", error);
    throw error;
  }
}

/**
 * Fetch a single market by ID
 * Backend will fetch from NeoFS first, then enrich with contract data
 */
export async function fetchMarket(
  marketId: string,
  useNeoFS: boolean = true
): Promise<Market | null> {
  try {
    const response = await fetch(
      `${API_BASE}/markets/${marketId}?use_neofs=${useNeoFS}`
    );
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch market: ${response.statusText}`);
    }

    const data = await response.json();
    if (data.success && data.market) {
      const m = data.market;
      return {
        id: m.id || m.market_id || marketId,
        question: m.question || m.Question || "",
        description: m.description || m.Description || "",
        category: m.category || m.Category || "Others",
        resolveDate: String(
          m.resolve_date || m.resolveDate || m.ResolveDate || ""
        ),
        probability: typeof m.probability === "number" ? m.probability : 50,
        volume:
          (typeof m.volume === "string" ? m.volume : undefined) ||
          formatVolume(
            typeof m.yes_shares === "number"
              ? m.yes_shares
              : typeof m.YesShares === "number"
              ? m.YesShares
              : 0,
            typeof m.no_shares === "number"
              ? m.no_shares
              : typeof m.NoShares === "number"
              ? m.NoShares
              : 0
          ),
        isResolved: Boolean(m.is_resolved || m.isResolved || m.Resolved),
        outcome: m.outcome || m.Outcome,
        creator: m.creator || m.Creator,
        created_at: m.created_at || m.createdAt || m.CreatedAt,
        oracle_url: m.oracle_url || m.oracleUrl || m.OracleUrl,
      };
    }
    return null;
  } catch (error) {
    console.error("Error fetching market:", error);
    throw error;
  }
}

/**
 * Create a new market
 * Backend will store in NeoFS after transaction confirmation
 */
export async function createMarket(marketData: MarketCreateRequest): Promise<{
  success: boolean;
  tx_data: Record<string, unknown>;
  message: string;
}> {
  try {
    const response = await fetch(`${API_BASE}/markets/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(marketData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        error.detail || `Failed to create market: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error creating market:", error);
    throw error;
  }
}

/**
 * Fetch market directly from NeoFS
 */
export async function fetchMarketFromNeoFS(
  marketId: string
): Promise<Market | null> {
  try {
    const response = await fetch(`${API_BASE}/neofs/markets/${marketId}`);
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch from NeoFS: ${response.statusText}`);
    }

    const data = await response.json();
    if (data.success && data.market) {
      const m = data.market;
      return {
        id: m.market_id || marketId,
        question: m.question || "",
        description: m.description || "",
        category: m.category || "Others",
        resolveDate: m.resolve_date || m.resolveDate || "",
        probability: m.probability || 50,
        volume: m.volume || "0",
        isResolved: m.status === "confirmed" || m.isResolved || false,
        creator: m.creator,
        created_at: m.created_at,
        oracle_url: m.oracle_url,
      };
    }
    return null;
  } catch (error) {
    console.error("Error fetching from NeoFS:", error);
    return null;
  }
}

/**
 * Format volume from shares
 */
function formatVolume(yesShares: number, noShares: number): string {
  const total = yesShares + noShares;
  if (total === 0) return "0";

  // Convert from smallest unit (divide by 10^8 for GAS)
  const totalGAS = total / 100000000;

  if (totalGAS >= 1000) {
    return `${(totalGAS / 1000).toFixed(1)}k`;
  }
  return totalGAS.toFixed(2);
}

/**
 * Agent Analysis Interfaces
 */
export interface AgentAnalysis {
  market_question: string;
  market_id?: string;
  analyses: Array<{
    probability: number;
    confidence: number;
    evidence: string;
    sources_count: number;
  }>;
  judgment: {
    consensus_probability: number;
    consensus_confidence: number;
    agent_count: number;
    agreement_level: string;
    reasoning: string;
  };
  trade_proposal: {
    action: "BUY_YES" | "BUY_NO";
    amount: number;
    confidence: number;
    reasoning: string;
  };
  summary: {
    consensus_probability: number;
    consensus_confidence: number;
    recommended_action: string;
    recommended_stake: number;
    agreement_level: string;
    analyses_count: number;
  };
}

export interface TradeProposal {
  action: "BUY_YES" | "BUY_NO";
  amount: number;
  confidence: number;
  reasoning: string;
}

/**
 * Trigger full agent analysis for a market
 * Runs: Analyzer → Trader → Judge (all 3 agents)
 */
export async function analyzeMarket(marketId: string): Promise<AgentAnalysis> {
  try {
    const response = await fetch(`${API_BASE}/markets/${marketId}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        error.detail || `Failed to analyze market: ${response.statusText}`
      );
    }

    const data = await response.json();
    if (data.success && data.analysis) {
      return data.analysis;
    }
    throw new Error("Invalid response format");
  } catch (error) {
    console.error("Error analyzing market:", error);
    throw error;
  }
}

/**
 * Get trade proposal from Trader agent
 */
export async function getTradeProposal(
  marketId: string,
  analysis?: Record<string, unknown>
): Promise<TradeProposal> {
  try {
    const response = await fetch(
      `${API_BASE}/markets/${marketId}/trade/propose`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(analysis || {}),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(
        error.detail || `Failed to get trade proposal: ${response.statusText}`
      );
    }

    const data = await response.json();
    if (data.success && data.trade_proposal) {
      return data.trade_proposal;
    }
    throw new Error("Invalid response format");
  } catch (error) {
    console.error("Error getting trade proposal:", error);
    throw error;
  }
}

/**
 * Connect to WebSocket for real-time agent logs
 */
export function connectAgentWebSocket(
  marketId: string,
  onMessage: (data: Record<string, unknown>) => void,
  onError?: (error: Event) => void
): WebSocket {
  const wsUrl = API_BASE.replace("http://", "ws://").replace(
    "https://",
    "wss://"
  );
  const ws = new WebSocket(`${wsUrl}/ws/agent-logs/${marketId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    if (onError) onError(error);
  };

  ws.onclose = () => {
    console.log("WebSocket connection closed");
  };

  return ws;
}
