"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentChat } from "@/components/features/AgentChat";
import { TradePanel } from "@/components/features/TradePanel";
import { ProbabilityGauge } from "@/components/features/ProbabilityGauge";
import {
  Share2,
  ExternalLink,
  Clock,
  User,
  Loader2,
  Brain,
  Sparkles,
} from "lucide-react";
import { getMarket, getProbability } from "@/lib/neoline";
import {
  analyzeMarket,
  getTradeProposal,
  type AgentAnalysis,
  type TradeProposal,
} from "@/lib/api";

// Helper function to format volume
function formatVolume(yesShares: number, noShares: number): string {
  const total = yesShares + noShares;
  if (total === 0) return "0";
  if (total < 1000) return total.toString();
  if (total < 1000000) return `${(total / 1000).toFixed(1)}K`;
  return `${(total / 1000000).toFixed(1)}M`;
}

export default function MarketDetailsPage() {
  const params = useParams();
  const id = params?.id as string;
  const [marketData, setMarketData] = useState<{
    question: string;
    description: string;
    category: string;
    creator: string;
    created: string;
    resolveDate: string;
    volume: string;
    probability: number;
    resolved: boolean;
    outcome?: string;
    oracleUrl: string;
    agentProbability?: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agentAnalysis, setAgentAnalysis] = useState<AgentAnalysis | null>(
    null
  );
  const [tradeProposal, setTradeProposal] = useState<TradeProposal | null>(
    null
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMarket = async () => {
      if (!id) return;

      setIsLoading(true);
      setError(null);

      try {
        // Fetch directly from contract using NeoLine
        console.log(
          `🔍 [MARKET DETAIL] Fetching market ${id} from contract...`
        );
        const marketDataArray = await getMarket(id);
        const probabilityValue = await getProbability(id);

        if (
          marketDataArray &&
          Array.isArray(marketDataArray) &&
          marketDataArray.length >= 11
        ) {
          // Helper to extract value from {type, value} structure
          const extractValue = (item: unknown): unknown => {
            if (item === null || item === undefined) return "";
            if (typeof item === "object" && "value" in item) {
              return item.value;
            }
            return item;
          };

          // Parse market data array
          // MarketData struct: [Question, Description, Category, ResolveDate, OracleUrl, Creator, CreatedAt, Resolved, Outcome, YesShares, NoShares]
          const question = String(extractValue(marketDataArray[0]) || "");
          const description = String(extractValue(marketDataArray[1]) || "");
          const category = String(extractValue(marketDataArray[2]) || "Others");
          const resolveDate = String(extractValue(marketDataArray[3]) || "0");
          const oracleUrl = String(extractValue(marketDataArray[4]) || "");
          const creator = String(extractValue(marketDataArray[5]) || "");
          const createdAt = String(extractValue(marketDataArray[6]) || "0");
          const resolved = Boolean(extractValue(marketDataArray[7]) || false);
          const outcome = extractValue(marketDataArray[8]);
          const yesShares = parseInt(
            String(extractValue(marketDataArray[9]) || "0"),
            10
          );
          const noShares = parseInt(
            String(extractValue(marketDataArray[10]) || "0"),
            10
          );

          // Calculate probability from shares or use contract probability
          const totalShares = yesShares + noShares;
          const calculatedProbability =
            totalShares > 0
              ? Math.round((yesShares / totalShares) * 100)
              : probabilityValue / 100; // Contract returns 0-10000, divide by 100

          // Format volume
          const volume = formatVolume(yesShares, noShares);

          // Format dates
          const resolveDateFormatted =
            resolveDate && resolveDate !== "0"
              ? new Date(parseInt(resolveDate, 10)).toLocaleDateString()
              : "Unknown";

          const createdFormatted =
            createdAt && createdAt !== "0"
              ? new Date(parseInt(createdAt, 10)).toLocaleDateString()
              : new Date().toLocaleDateString();

          setMarketData({
            question: question,
            description: description || "No description",
            category: category,
            creator: creator
              ? creator.slice(0, 6) + "..." + creator.slice(-4)
              : "Unknown",
            created: createdFormatted,
            resolveDate: resolveDateFormatted,
            volume: volume,
            probability: calculatedProbability,
            resolved: resolved,
            outcome:
              outcome === true || outcome === "Yes"
                ? "Yes"
                : outcome === false || outcome === "No"
                ? "No"
                : undefined,
            oracleUrl: oracleUrl,
          });
          console.log(`✅ [MARKET DETAIL] Market ${id} loaded successfully`);
        } else {
          console.error(
            `❌ [MARKET DETAIL] Market ${id} returned invalid data:`,
            marketDataArray
          );
          setError("Market not found");
        }
      } catch (err) {
        console.error("Error fetching market:", err);
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load market";
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMarket();
  }, [id]);

  // Fetch agent analysis and trade proposal
  useEffect(() => {
    const fetchAgentData = async () => {
      if (!id) return;

      try {
        // Try to get trade proposal
        const proposal = await getTradeProposal(id);
        setTradeProposal(proposal);
      } catch (err) {
        // Trade proposal might not be available yet, that's okay
        console.log("Trade proposal not available yet");
      }
    };

    fetchAgentData();
  }, [id]);

  const handleAnalyzeMarket = async () => {
    if (!id) return;

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const analysis = await analyzeMarket(id);
      setAgentAnalysis(analysis);

      // Update trade proposal if available
      if (analysis.trade_proposal) {
        setTradeProposal(analysis.trade_proposal);
      }

      // Update probability if available
      if (analysis.summary?.consensus_probability && marketData) {
        setMarketData({
          ...marketData,
          agentProbability: analysis.summary.consensus_probability * 100,
        });
      }
    } catch (err) {
      console.error("Error analyzing market:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to analyze market";
      setAnalysisError(errorMessage);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading market...</span>
      </div>
    );
  }

  if (error || !marketData) {
    return (
      <div className="text-center py-20">
        <p className="text-destructive">{error || "Market not found"}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start gap-6">
        <div className="space-y-4 flex-1">
          <div className="flex gap-2">
            <Badge
              variant="outline"
              className="bg-primary/10 text-primary border-primary/20"
            >
              {marketData.category}
            </Badge>
            <Badge variant={marketData.resolved ? "default" : "secondary"}>
              {marketData.resolved ? "Resolved" : "Open"}
            </Badge>
            {marketData.resolved && marketData.outcome && (
              <Badge
                variant={
                  marketData.outcome === "Yes" ? "default" : "destructive"
                }
              >
                {marketData.outcome}
              </Badge>
            )}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold leading-tight">
            {marketData.question}
          </h1>
          <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4" />
              <span className="font-mono text-xs bg-secondary px-2 py-1 rounded">
                {marketData.creator}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>Resolves: {marketData.resolveDate}</span>
            </div>
            {marketData.oracleUrl && (
              <div className="flex items-center gap-2 text-accent">
                <ExternalLink className="w-4 h-4" />
                <a
                  href={marketData.oracleUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  Oracle Source
                </a>
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleAnalyzeMarket}
            disabled={isAnalyzing}
            className="gap-2"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4" />
                Analyze Market
              </>
            )}
          </Button>
          <Button variant="outline" size="icon">
            <Share2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {analysisError && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
          {analysisError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Column: Gauge & Chat */}
        <div className="lg:col-span-2 space-y-8">
          {/* Probability Hero */}
          <div className="flex flex-col md:flex-row items-center justify-between bg-card border border-border rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-transparent" />
            <div className="z-10">
              <ProbabilityGauge probability={marketData.probability} />
            </div>
            <div className="z-10 max-w-sm space-y-4 text-center md:text-left mt-6 md:mt-0">
              <h3 className="text-xl font-bold">Market Sentiment</h3>
              <p className="text-muted-foreground text-sm">
                Current probability based on market shares.
              </p>
              <div className="flex gap-4 justify-center md:justify-start">
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">
                    {marketData.volume}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Total Volume
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Agent Chat / Debate */}
          <AgentChat marketId={id} />

          {/* Description & Evidence */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold">Market Rules & Evidence</h3>
            <div className="prose prose-invert max-w-none bg-secondary/20 p-6 rounded-xl border border-border/50">
              <p>{marketData.description}</p>
              {marketData.oracleUrl && (
                <>
                  <h4>Resolution Source</h4>
                  <ul>
                    <li>
                      <a
                        href={marketData.oracleUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent hover:underline"
                      >
                        {marketData.oracleUrl}
                      </a>
                    </li>
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar: Trade Panel */}
        <div className="space-y-6">
          <TradePanel marketId={id || "1"} />

          {tradeProposal ? (
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <h4 className="font-bold text-blue-400">Agent Signal</h4>
              </div>
              <p className="text-sm text-blue-200 mb-2">
                SpoonOS &quot;Trader&quot; agent recommends{" "}
                <strong className="text-white">
                  {tradeProposal.action === "BUY_YES" ? "BUY YES" : "BUY NO"}
                </strong>{" "}
                for {tradeProposal.amount.toFixed(2)} GAS.
              </p>
              <p className="text-xs text-blue-300/80 mb-2">
                Confidence: {(tradeProposal.confidence * 100).toFixed(0)}%
              </p>
              {tradeProposal.reasoning && (
                <p className="text-xs text-blue-300/60 italic">
                  &ldquo;{tradeProposal.reasoning}&rdquo;
                </p>
              )}
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-muted/20 border border-border">
              <h4 className="font-bold text-muted-foreground mb-2">
                Agent Signal
              </h4>
              <p className="text-sm text-muted-foreground">
                No agent analysis yet. Click "Analyze Market" to get
                recommendations.
              </p>
            </div>
          )}

          {agentAnalysis && (
            <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20">
              <h4 className="font-bold text-green-400 mb-2">
                Analysis Summary
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">
                    Consensus Probability:
                  </span>
                  <span className="font-bold text-green-400">
                    {(
                      agentAnalysis.summary.consensus_probability * 100
                    ).toFixed(1)}
                    %
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Confidence:</span>
                  <span className="font-bold text-green-400">
                    {(agentAnalysis.summary.consensus_confidence * 100).toFixed(
                      0
                    )}
                    %
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Agreement:</span>
                  <span className="font-bold text-green-400 capitalize">
                    {agentAnalysis.summary.agreement_level}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Analyses:</span>
                  <span className="font-bold text-green-400">
                    {agentAnalysis.summary.analyses_count}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
