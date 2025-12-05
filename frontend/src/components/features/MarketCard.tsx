"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge"; // Need to create Badge
import { Users, Clock, TrendingUp } from "lucide-react";

interface MarketCardProps {
  id: string;
  question: string;
  category: string;
  resolveDate: string;
  probability: number;
  volume: string;
  isResolved?: boolean;
  outcome?: "Yes" | "No";
}

export function MarketCard({
  id,
  question,
  category,
  resolveDate,
  probability,
  volume,
  isResolved,
  outcome,
}: MarketCardProps) {
  return (
    <Link href={`/markets/${id}`}>
      <Card className="group hover:neon-border transition-all duration-300 cursor-pointer bg-card border-border overflow-hidden h-full flex flex-col">
        <div
          className={`h-1 ${
            isResolved ? "bg-muted" : "bg-gradient-to-r from-primary to-accent"
          }`}
        />
        <CardHeader className="pb-2 flex-1">
          <div className="flex justify-between items-start mb-2">
            <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded uppercase tracking-wider">
              {category}
            </span>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{resolveDate}</span>
            </div>
          </div>
          <CardTitle className="text-lg leading-snug group-hover:text-primary transition-colors">
            {question}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="space-y-4 mt-2">
            {isResolved ? (
              <div className="flex items-center justify-between p-2 bg-muted/50 rounded-lg border border-border">
                <span className="text-sm text-muted-foreground">Outcome</span>
                <span
                  className={`font-bold ${
                    outcome === "Yes" ? "text-primary" : "text-destructive"
                  }`}
                >
                  {outcome}
                </span>
              </div>
            ) : (
              <>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Yes Probability</span>
                  <span className="font-bold text-primary">{probability}%</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{ width: `${probability}%` }}
                  />
                </div>
              </>
            )}

            <div className="flex justify-between items-center pt-3 border-t border-border/50">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Users className="w-3 h-3" />
                <span>12 Judges</span>
              </div>
              <div className="flex items-center gap-1 text-xs font-mono text-accent">
                <TrendingUp className="w-3 h-3" />
                <span>{volume} GAS</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
