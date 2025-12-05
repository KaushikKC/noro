"use client";

import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AgentChat } from "@/components/features/AgentChat";
import { TradePanel } from "@/components/features/TradePanel";
import { ProbabilityGauge } from "@/components/features/ProbabilityGauge";
import { Share2, ExternalLink, Clock, User } from "lucide-react";

export default function MarketDetailsPage() {
  // In a real app, we'd fetch data based on this ID
  const params = useParams();
  const id = params?.id as string;

  const marketData = {
    question: "Will CRISPR therapy for sickle cell be FDA approved by Q3 2025?",
    description: "This market resolves to YES if the FDA grants marketing approval for a CRISPR-Cas9 based therapy for sickle cell disease by September 30, 2025. Evidence will be based on FDA press releases and official announcements.",
    creator: "0x7a...39b2",
    created: "2024-02-10",
    resolveDate: "2025-09-30",
    volume: "12,402 GAS",
    probability: 78
  };

  return (
    <div className="space-y-8 pb-20">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start gap-6">
        <div className="space-y-4 flex-1">
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">Biology</Badge>
            <Badge variant="secondary">Open</Badge>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold leading-tight">
            {marketData.question}
          </h1>
          <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4" />
              <span className="font-mono text-xs bg-secondary px-2 py-1 rounded">{marketData.creator}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>Resolves: {marketData.resolveDate}</span>
            </div>
            <div className="flex items-center gap-2 text-accent">
              <ExternalLink className="w-4 h-4" />
              <a href="#" className="hover:underline">View Contract</a>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon">
            <Share2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

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
                Aggregated probability based on 12 agent judges and 1,204 active traders. The trend is bullish based on recent clinical trial data.
              </p>
              <div className="flex gap-4 justify-center md:justify-start">
                 <div className="text-center">
                   <div className="text-2xl font-bold text-primary">+12%</div>
                   <div className="text-xs text-muted-foreground">24h Change</div>
                 </div>
                 <div className="text-center">
                   <div className="text-2xl font-bold text-white">{marketData.volume}</div>
                   <div className="text-xs text-muted-foreground">Total Volume</div>
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
               <h4>Resolution Sources</h4>
               <ul>
                 <li>FDA.gov official press releases</li>
                 <li>SEC filings from relevant biotech companies</li>
                 <li>Nature Medicine journal publications</li>
               </ul>
             </div>
          </div>
        </div>

        {/* Sidebar: Trade Panel */}
        <div className="space-y-6">
          <TradePanel />
          
          <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
             <h4 className="font-bold text-blue-400 mb-2">Agent Signal</h4>
             <p className="text-sm text-blue-200">
               SpoonOS "Trader" agent recommends <strong>BUY YES</strong> based on recent patent approval news. Confidence: 92%.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
}

