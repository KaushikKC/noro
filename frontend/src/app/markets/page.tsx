"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { MarketCard } from "@/components/features/MarketCard";
import { Search, Filter, SlidersHorizontal } from "lucide-react";

// Mock Data
const MARKETS = [
  {
    id: "1",
    question: "Will CRISPR therapy for sickle cell be FDA approved by Q3 2025?",
    category: "Biology",
    resolveDate: "Dec 31, 2025",
    probability: 78,
    volume: "1.2k",
    isResolved: false
  },
  {
    id: "2",
    question: "Will global temperatures exceed 1.5°C above pre-industrial levels in 2024?",
    category: "Climate",
    resolveDate: "Jan 15, 2025",
    probability: 92,
    volume: "5.4k",
    isResolved: false
  },
  {
    id: "3",
    question: "Will SpaceX Starship achieve orbit by June 2024?",
    category: "Physics",
    resolveDate: "Jun 30, 2024",
    probability: 45,
    volume: "890",
    isResolved: true,
    outcome: "Yes" as const
  },
  {
    id: "4",
    question: "Will a new room-temperature superconductor be verified by Nature?",
    category: "Physics",
    resolveDate: "Oct 1, 2025",
    probability: 12,
    volume: "12.5k",
    isResolved: false
  },
  {
    id: "5",
    question: "Will FDA approve the first anti-aging drug by 2030?",
    category: "Biology",
    resolveDate: "Jan 1, 2030",
    probability: 34,
    volume: "2.1k",
    isResolved: false
  },
];

export default function MarketsPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const filteredMarkets = MARKETS.filter(m => 
    m.question.toLowerCase().includes(search.toLowerCase()) &&
    (filter === "all" || 
     (filter === "open" && !m.isResolved) || 
     (filter === "resolved" && m.isResolved) ||
     (filter === m.category.toLowerCase()))
  );

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Markets</h1>
          <p className="text-muted-foreground">Explore and trade on scientific outcomes.</p>
        </div>
        <div className="flex items-center gap-2">
           <Button variant="outline" className="gap-2">
             <SlidersHorizontal className="w-4 h-4" /> Sort
           </Button>
           <Button className="bg-primary text-black font-bold">Create Market</Button>
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
          {["all", "open", "resolved", "biology", "climate", "physics"].map((f) => (
            <Button
              key={f}
              variant={filter === f ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f)}
              className="capitalize whitespace-nowrap"
            >
              {f}
            </Button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredMarkets.map((market) => (
          <MarketCard key={market.id} {...market} />
        ))}
      </div>
      
      {filteredMarkets.length === 0 && (
        <div className="text-center py-20 text-muted-foreground">
          No markets found matching your criteria.
        </div>
      )}
    </div>
  );
}

