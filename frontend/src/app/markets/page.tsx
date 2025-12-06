"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MarketCard } from "@/components/features/MarketCard";
import { Search, SlidersHorizontal, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { fetchAllMarketsFromContract } from "@/lib/neoline";
import { fetchMarkets } from "@/lib/api";

export default function MarketsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  // Market type for MarketCard (simplified)
  type MarketCardData = {
    id: string;
    question: string;
    category: string;
    resolveDate: string;
    probability: number;
    volume: string;
    isResolved: boolean;
    outcome?: "Yes" | "No";
  };

  const [markets, setMarkets] = useState<MarketCardData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch markets from backend API (contract only, no NeoFS for now)
  useEffect(() => {
    const loadMarkets = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Try backend API first (fetches from NeoFS + enriches with contract data)
        // Fallback to direct contract fetch if backend fails
        console.log(
          "🔍 [MARKETS PAGE] Fetching markets from backend API (NeoFS + contract)..."
        );
        let fetchedMarkets;

        try {
          // fetchMarkets returns Market[] directly, not a response object
          fetchedMarkets = await fetchMarkets();
          console.log(
            "✅ [MARKETS PAGE] Fetched from backend API (NeoFS + contract):",
            fetchedMarkets
          );
        } catch (apiError) {
          console.warn(
            "⚠️ [MARKETS PAGE] Backend API failed, falling back to direct contract fetch:",
            apiError
          );
          // Fallback to direct contract fetch
          fetchedMarkets = await fetchAllMarketsFromContract();
          console.log(
            "✅ [MARKETS PAGE] Fetched from contract (fallback):",
            fetchedMarkets
          );
        }

        if (fetchedMarkets && fetchedMarkets.length > 0) {
          // The API already normalizes the data, but we need to format it for MarketCard
          const normalizedMarkets = fetchedMarkets.map((m: any) => {
            // Format resolve date
            let resolveDateStr = "";
            if (m.resolveDate || m.resolve_date) {
              const dateValue = m.resolveDate || m.resolve_date;
              // If it's a timestamp (number or string), convert to date
              const timestamp =
                typeof dateValue === "number"
                  ? dateValue
                  : parseInt(dateValue, 10);
              if (!isNaN(timestamp) && timestamp > 0) {
                // Handle both seconds and milliseconds timestamps
                const date =
                  timestamp > 1000000000000
                    ? new Date(timestamp)
                    : new Date(timestamp * 1000);
                resolveDateStr = date.toLocaleDateString();
              } else {
                resolveDateStr = String(dateValue);
              }
            } else {
              resolveDateStr = new Date().toLocaleDateString();
            }

            // Convert outcome to "Yes" | "No" | undefined
            let outcome: "Yes" | "No" | undefined = m.outcome;

            const marketCard: MarketCardData = {
              id: m.id || "",
              question: m.question || "",
              category: m.category || "Others",
              resolveDate: resolveDateStr,
              probability:
                typeof m.probability === "number" ? m.probability : 50,
              volume: m.volume || "0",
              isResolved: m.isResolved || m.is_resolved || false,
              outcome: outcome,
            };
            return marketCard;
          });
          setMarkets(normalizedMarkets);
        } else {
          // No markets yet, show empty state
          setMarkets([]);
        }
      } catch (err) {
        console.error("Error fetching markets:", err);
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load markets";
        setError(errorMessage);
        // Fallback to empty array (don't show mock data)
        setMarkets([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadMarkets();
  }, []);

  const filteredMarkets = markets.filter((m) => {
    // Safely handle question and category - ensure they're strings
    const question =
      typeof m.question === "string" ? m.question : String(m.question || "");
    const category =
      typeof m.category === "string" ? m.category : String(m.category || "");

    return (
      question.toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" ||
        (filter === "open" && !m.isResolved) ||
        (filter === "resolved" && m.isResolved) ||
        filter === category.toLowerCase())
    );
  });

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Markets</h1>
          <p className="text-muted-foreground">
            Explore and trade on scientific outcomes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2">
            <SlidersHorizontal className="w-4 h-4" /> Sort
          </Button>
          <Button
            className="bg-primary text-black font-bold"
            onClick={() => router.push("/create")}
          >
            Create Market
          </Button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 bg-card/50 p-4 rounded-xl border border-border">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search markets..."
            className="pl-9 bg-background"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
          {["all", "open", "resolved", "biology", "climate", "physics"].map(
            (f) => (
              <Button
                key={f}
                variant={filter === f ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter(f)}
                className="capitalize whitespace-nowrap"
              >
                {f}
              </Button>
            )
          )}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading markets...</span>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
          {error}
        </div>
      )}

      {/* Markets Grid */}
      {!isLoading && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredMarkets.map((market) => (
              <MarketCard key={market.id} {...market} />
            ))}
          </div>

          {filteredMarkets.length === 0 && (
            <div className="text-center py-20 text-muted-foreground">
              {markets.length === 0
                ? "No markets created yet. Be the first to create one!"
                : "No markets found matching your criteria."}
            </div>
          )}
        </>
      )}
    </div>
  );
}
