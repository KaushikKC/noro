"use client";

import { useParams, useRouter } from "next/navigation";
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
  analyzeMarketTest,
  getTradeProposal,
  fetchMarket,
  demoResolveMarket,
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
  const router = useRouter();
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
    neofsObjectId?: string;
    neofsUrl?: string;
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
  const [isResolving, setIsResolving] = useState(false);

  useEffect(() => {
    const loadMarket = async () => {
      if (!id) return;

      setIsLoading(true);
      setError(null);

      try {
        // TEST MODE: Handle all test markets with their specific data
        const testMarkets: Record<
          string,
          {
            question: string;
            description: string;
            category: string;
            creator: string;
            created: string;
            resolveDate: string;
            volume: string;
            probability: number;
            resolved: boolean;
            oracleUrl: string;
          }
        > = {
          test: {
            question: "Will it rain in London, UK on December 25, 2024?",
            description: "Test market for agent analysis - Weather prediction",
            category: "Climate",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "December 25, 2024",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl:
              "https://www.metoffice.gov.uk/weather/forecast/gcpvj0v07",
          },
          test_1: {
            question: "Will it rain in London, UK on December 25, 2024?",
            description: "Test market for agent analysis - Weather prediction",
            category: "Climate",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "December 25, 2024",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl:
              "https://www.metoffice.gov.uk/weather/forecast/gcpvj0v07",
          },
          test_2: {
            question:
              "Will Bitcoin (BTC) price exceed $100,000 by January 1, 2025?",
            description:
              "Test market for agent analysis - Cryptocurrency price prediction",
            category: "Crypto",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "January 1, 2025",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl:
              "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
          },
          test_3: {
            question:
              "Will a new room-temperature superconductor be verified by Nature journal by 2025?",
            description:
              "Test market for agent analysis - Scientific breakthrough prediction",
            category: "Physics",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "December 31, 2025",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl:
              "https://www.nature.com/search?q=room+temperature+superconductor",
          },
          test_4: {
            question:
              "Will the 2024 Paris Olympics have more than 10,000 athletes participating?",
            description:
              "Test market for agent analysis - Sports event prediction",
            category: "Sports",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "August 11, 2024",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl: "https://olympics.com/en/paris-2024/",
          },
          test_5: {
            question:
              "Will global average temperature exceed 1.5°C above pre-industrial levels in 2024?",
            description:
              "Test market for agent analysis - Climate change prediction",
            category: "Climate",
            creator: "Test User",
            created: new Date().toLocaleDateString(),
            resolveDate: "December 31, 2024",
            volume: "0",
            probability: 50,
            resolved: false,
            oracleUrl:
              "https://climate.nasa.gov/vital-signs/global-temperature/",
          },
        };

        if (id.startsWith("test")) {
          const testMarket = testMarkets[id] || testMarkets.test;
          console.log(`🧪 [TEST MODE] Using test market: ${id}`, testMarket);
          setMarketData(testMarket);
          setError(null); // Clear any errors
          setIsLoading(false);
          return;
        }

        // Fetch from database via backend API
        console.log(
          `🔍 [MARKET DETAIL] Fetching market ${id} from database...`
        );

        // Try fetching from backend API first (database)
        let backendMarket: Awaited<ReturnType<typeof fetchMarket>> = null;
        try {
          console.log(
            `🔍 [MARKET DETAIL] Calling fetchMarket(${id}, false)...`
          );
          backendMarket = await fetchMarket(id, false);
          console.log(
            `✅ [MARKET DETAIL] Fetched from database:`,
            backendMarket
              ? `Found market: ${backendMarket.question?.substring(0, 50)}`
              : "null/undefined"
          );
        } catch (err) {
          console.error(`❌ [MARKET DETAIL] Backend fetch error:`, err);
          console.log(
            `⚠️ [MARKET DETAIL] Backend fetch failed, trying contract...`
          );
        }

        // Fallback to contract if backend fails
        let marketDataArray: unknown = null;
        let probabilityValue = 50;
        if (!backendMarket) {
          console.log(
            `🔍 [MARKET DETAIL] Fetching from contract as fallback...`
          );
          marketDataArray = await getMarket(id);
          probabilityValue = await getProbability(id);
        }

        // Use backend data if available
        if (backendMarket) {
          // Format dates
          const resolveDateFormatted = backendMarket.resolveDate
            ? new Date(backendMarket.resolveDate).toLocaleDateString()
            : "Unknown";

          const createdFormatted = backendMarket.created_at
            ? new Date(backendMarket.created_at).toLocaleDateString()
            : new Date().toLocaleDateString();

          // Type assertion for NeoFS fields
          const marketWithNeoFS = backendMarket as typeof backendMarket & {
            neofs_object_id?: string;
            neofs_url?: string;
          };

          setMarketData({
            question: backendMarket.question || "",
            description: backendMarket.description || "No description",
            category: backendMarket.category || "Others",
            creator: backendMarket.creator
              ? backendMarket.creator.slice(0, 6) +
                "..." +
                backendMarket.creator.slice(-4)
              : "Unknown",
            created: createdFormatted,
            resolveDate: resolveDateFormatted,
            volume: backendMarket.volume || "0",
            probability: backendMarket.probability || 50,
            resolved: backendMarket.isResolved || false,
            outcome:
              backendMarket.outcome === true || backendMarket.outcome === "Yes"
                ? "Yes"
                : backendMarket.outcome === false ||
                  backendMarket.outcome === "No"
                ? "No"
                : undefined,
            oracleUrl: backendMarket.oracle_url || "",
            neofsObjectId: marketWithNeoFS.neofs_object_id || undefined,
            neofsUrl: marketWithNeoFS.neofs_url || undefined,
          });
          console.log(`✅ [MARKET DETAIL] Market ${id} loaded from database`);
        } else if (
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

    loadMarket();
  }, [id]);

  // Fetch agent analysis and trade proposal
  useEffect(() => {
    const fetchAgentData = async () => {
      if (!id) return;

      // Skip trade proposal fetch for test markets - it will come from analysis
      if (id.startsWith("test")) {
        console.log("⚠️ Skipping trade proposal fetch for test market");
        return;
      }

      try {
        // Try to get trade proposal (only for real markets)
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
      let analysis: AgentAnalysis;

      // If market data is available, use it; otherwise use test endpoint with question
      if (marketData && marketData.question) {
        console.log("🧪 Using test endpoint with market data:", {
          question: marketData.question,
          oracleUrl: marketData.oracleUrl,
        });

        // Use test endpoint with question and oracle URL
        analysis = await analyzeMarketTest(
          marketData.question,
          marketData.oracleUrl,
          id
        );
      } else {
        // Fallback to regular endpoint
        console.log("📊 Using regular analyze endpoint for market:", id);
        analysis = await analyzeMarket(id);
      }

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

  const handleResolveMarket = async (outcome: "yes" | "no") => {
    if (!id) return;

    setIsResolving(true);
    try {
      const result = await demoResolveMarket(id, outcome);
      console.log("✅ Market resolved:", result);

      // Reload market data to show updated resolution status
      const updatedMarket = await fetchMarket(id, false);
      if (updatedMarket) {
        const marketWithNeoFS = updatedMarket as typeof updatedMarket & {
          neofs_object_id?: string;
          neofs_url?: string;
        };

        setMarketData({
          question: updatedMarket.question || "",
          description: updatedMarket.description || "No description",
          category: updatedMarket.category || "Others",
          creator: updatedMarket.creator
            ? updatedMarket.creator.slice(0, 6) +
              "..." +
              updatedMarket.creator.slice(-4)
            : "Unknown",
          created: updatedMarket.created_at
            ? new Date(updatedMarket.created_at).toLocaleDateString()
            : new Date().toLocaleDateString(),
          resolveDate: updatedMarket.resolveDate
            ? new Date(updatedMarket.resolveDate).toLocaleDateString()
            : "Unknown",
          volume: updatedMarket.volume || "0",
          probability: updatedMarket.probability || 50,
          resolved: updatedMarket.isResolved || false,
          outcome:
            updatedMarket.outcome === true || updatedMarket.outcome === "Yes"
              ? "Yes"
              : updatedMarket.outcome === false ||
                updatedMarket.outcome === "No"
              ? "No"
              : undefined,
          oracleUrl: updatedMarket.oracle_url || "",
          neofsObjectId: marketWithNeoFS.neofs_object_id || undefined,
          neofsUrl: marketWithNeoFS.neofs_url || undefined,
        });
      }
    } catch (err) {
      console.error("Error resolving market:", err);
      alert(
        `Failed to resolve market: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setIsResolving(false);
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
            {marketData.neofsUrl && (
              <div className="flex items-center gap-2 text-green-400">
                <ExternalLink className="w-4 h-4" />
                <a
                  href={marketData.neofsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                  title={`NeoFS Object ID: ${
                    marketData.neofsObjectId || "N/A"
                  }`}
                >
                  View on NeoFS
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
          {!marketData.resolved && (
            <div className="flex gap-2">
              <Button
                onClick={() => handleResolveMarket("yes")}
                disabled={isResolving}
                variant="outline"
                className="gap-2 bg-green-500/10 hover:bg-green-500/20 border-green-500/30 text-green-400"
              >
                {isResolving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "✅ Resolve YES"
                )}
              </Button>
              <Button
                onClick={() => handleResolveMarket("no")}
                disabled={isResolving}
                variant="outline"
                className="gap-2 bg-red-500/10 hover:bg-red-500/20 border-red-500/30 text-red-400"
              >
                {isResolving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "❌ Resolve NO"
                )}
              </Button>
            </div>
          )}
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

      {/* Test Market Selector - Only show for test markets */}
      {(id?.startsWith("test") || id === "test") && (
        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-5 h-5 text-blue-400" />
            <h3 className="font-bold text-blue-400">Test Market Examples</h3>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Switch between different test markets to see agent analysis on
            various topics:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            <Button
              variant={id === "test_1" ? "default" : "outline"}
              size="sm"
              onClick={() => router.push("/markets/test_1")}
              className="text-xs"
            >
              Weather
            </Button>
            <Button
              variant={id === "test_2" ? "default" : "outline"}
              size="sm"
              onClick={() => router.push("/markets/test_2")}
              className="text-xs"
            >
              Crypto (BTC)
            </Button>
            <Button
              variant={id === "test_3" ? "default" : "outline"}
              size="sm"
              onClick={() => router.push("/markets/test_3")}
              className="text-xs"
            >
              Science
            </Button>
            <Button
              variant={id === "test_4" ? "default" : "outline"}
              size="sm"
              onClick={() => router.push("/markets/test_4")}
              className="text-xs"
            >
              Sports
            </Button>
            <Button
              variant={id === "test_5" ? "default" : "outline"}
              size="sm"
              onClick={() => router.push("/markets/test_5")}
              className="text-xs"
            >
              Climate
            </Button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Column: Gauge & Chat */}
        <div className="lg:col-span-2 space-y-8">
          {/* Probability Hero */}
          <div className="flex flex-col md:flex-row items-center justify-between bg-card border border-border rounded-2xl p-8 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-transparent" />
            <div className="z-10">
              <ProbabilityGauge
                probability={
                  agentAnalysis?.summary?.consensus_probability
                    ? Math.round(
                        agentAnalysis.summary.consensus_probability * 100
                      )
                    : marketData.probability
                }
              />
            </div>
            <div className="z-10 max-w-sm space-y-4 text-center md:text-left mt-6 md:mt-0">
              <h3 className="text-xl font-bold">
                {agentAnalysis?.summary?.consensus_probability
                  ? "Agent Consensus Probability"
                  : "Market Sentiment"}
              </h3>
              <p className="text-muted-foreground text-sm">
                {agentAnalysis?.summary?.consensus_probability
                  ? `Based on ${
                      agentAnalysis.summary.analyses_count
                    } agent analyses with ${Math.round(
                      agentAnalysis.summary.consensus_confidence * 100
                    )}% confidence`
                  : "Current probability based on market shares."}
              </p>
              {agentAnalysis?.trade_proposal && (
                <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border-2 border-blue-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <h4 className="font-bold text-lg text-blue-400">
                      Agent Recommendation
                    </h4>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        agentAnalysis.trade_proposal.action === "BUY_YES"
                          ? "default"
                          : "destructive"
                      }
                      className="text-lg px-4 py-2"
                    >
                      {agentAnalysis.trade_proposal.action === "BUY_YES"
                        ? "BUY YES"
                        : "BUY NO"}
                    </Badge>
                    <span className="text-white font-bold">
                      {agentAnalysis.trade_proposal.amount.toFixed(2)} GAS
                    </span>
                    <span className="text-muted-foreground text-sm">
                      (
                      {Math.round(
                        agentAnalysis.trade_proposal.confidence * 100
                      )}
                      % confidence)
                    </span>
                  </div>
                  {agentAnalysis.trade_proposal.reasoning && (
                    <p className="text-sm text-muted-foreground mt-2 italic">
                      &quot;{agentAnalysis.trade_proposal.reasoning}&quot;
                    </p>
                  )}
                </div>
              )}
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
          <AgentChat marketId={id} analysis={agentAnalysis} />

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
              {marketData.neofsObjectId && (
                <>
                  <h4 className="mt-4">NeoFS Storage</h4>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <span className="text-muted-foreground">Object ID: </span>
                      <code className="bg-secondary/50 px-2 py-1 rounded text-xs font-mono">
                        {marketData.neofsObjectId}
                      </code>
                    </div>
                    {marketData.neofsUrl && (
                      <div>
                        <a
                          href={marketData.neofsUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-400 hover:underline flex items-center gap-2"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Download from NeoFS
                        </a>
                      </div>
                    )}
                  </div>
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
                No agent analysis yet. Click &quot;Analyze Market&quot; to get
                recommendations.
              </p>
            </div>
          )}

          {agentAnalysis && (
            <div className="p-5 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border-2 border-green-500/40 shadow-lg">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="w-5 h-5 text-green-400" />
                <h4 className="font-bold text-lg text-green-400">
                  Analysis Summary
                </h4>
              </div>
              <div className="space-y-3">
                <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-muted-foreground">
                      Consensus Probability:
                    </span>
                    <span className="text-2xl font-bold text-green-400">
                      {(
                        agentAnalysis.summary.consensus_probability * 100
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden mt-2">
                    <div
                      className="h-full bg-green-400 transition-all duration-500"
                      style={{
                        width: `${
                          agentAnalysis.summary.consensus_probability * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 bg-black/20 rounded border border-border/50">
                    <div className="text-xs text-muted-foreground mb-1">
                      Confidence
                    </div>
                    <div className="text-lg font-bold text-green-400">
                      {(
                        agentAnalysis.summary.consensus_confidence * 100
                      ).toFixed(0)}
                      %
                    </div>
                  </div>
                  <div className="p-2 bg-black/20 rounded border border-border/50">
                    <div className="text-xs text-muted-foreground mb-1">
                      Agreement
                    </div>
                    <div className="text-lg font-bold text-green-400 capitalize">
                      {agentAnalysis.summary.agreement_level}
                    </div>
                  </div>
                </div>
                <div className="p-2 bg-black/20 rounded border border-border/50 text-center">
                  <div className="text-xs text-muted-foreground mb-1">
                    Agent Analyses
                  </div>
                  <div className="text-lg font-bold text-green-400">
                    {agentAnalysis.summary.analyses_count} agents analyzed
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
