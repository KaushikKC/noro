"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  BrainCircuit,
  Gavel,
  Play,
  FileText,
  Download,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  analyzeMarket,
  connectAgentWebSocket,
  type AgentAnalysis,
} from "@/lib/api";

type AgentRole = "Analyzer" | "Trader" | "Judge";

interface AgentMessage {
  id: string;
  agent: AgentRole;
  type: "analysis" | "trade" | "verdict";
  content: string;
  confidence: number;
  timestamp: number;
  attachments?: { type: string; neoFsHash: string }[];
}

export function AgentChat({ marketId }: { marketId: string }) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Convert agent analysis to messages
  const convertAnalysisToMessages = (
    analysis: AgentAnalysis
  ): AgentMessage[] => {
    const msgs: AgentMessage[] = [];

    // Analyzer messages
    analysis.analyses.forEach((a, idx) => {
      msgs.push({
        id: `analyzer-${idx}`,
        agent: "Analyzer",
        type: "analysis",
        content:
          a.evidence ||
          `Analysis ${idx + 1}: Probability ${(a.probability * 100).toFixed(
            1
          )}% based on ${a.sources_count} sources.`,
        confidence: a.confidence,
        timestamp: Date.now() - (analysis.analyses.length - idx) * 10000,
      });
    });

    // Judge message
    if (analysis.judgment) {
      msgs.push({
        id: "judge-consensus",
        agent: "Judge",
        type: "verdict",
        content:
          analysis.judgment.reasoning ||
          `Consensus: ${(analysis.judgment.consensus_probability * 100).toFixed(
            1
          )}% probability with ${(
            analysis.judgment.consensus_confidence * 100
          ).toFixed(0)}% confidence. Agreement level: ${
            analysis.judgment.agreement_level
          }.`,
        confidence: analysis.judgment.consensus_confidence,
        timestamp: Date.now() - 5000,
      });
    }

    // Trader message
    if (analysis.trade_proposal) {
      msgs.push({
        id: "trader-proposal",
        agent: "Trader",
        type: "trade",
        content:
          analysis.trade_proposal.reasoning ||
          `${analysis.trade_proposal.action} ${
            analysis.trade_proposal.amount
          } GAS. ${(analysis.trade_proposal.confidence * 100).toFixed(
            0
          )}% confidence.`,
        confidence: analysis.trade_proposal.confidence,
        timestamp: Date.now(),
      });
    }

    return msgs;
  };

  // Fetch initial analysis
  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!marketId) return;

      setIsLoading(true);
      setError(null);

      try {
        const analysis = await analyzeMarket(marketId);
        const msgs = convertAnalysisToMessages(analysis);
        setMessages(msgs);
      } catch (err: any) {
        console.error("Error fetching analysis:", err);
        setError(err.message || "Failed to load agent analysis");
        // Show empty state message
        setMessages([
          {
            id: "error",
            agent: "Analyzer",
            type: "analysis",
            content:
              "No analysis available yet. Click 'Analyze Market' to run agents.",
            confidence: 0,
            timestamp: Date.now(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [marketId]);

  // Connect WebSocket for real-time updates
  useEffect(() => {
    if (!marketId) return;

    try {
      const ws = connectAgentWebSocket(
        marketId,
        (data) => {
          setIsConnected(true);
          if (data.type === "full_analysis" && data.data) {
            const msgs = convertAnalysisToMessages(data.data);
            setMessages(msgs);
          } else if (data.type === "agent_update") {
            // Add individual agent update
            const newMsg: AgentMessage = {
              id: `update-${Date.now()}`,
              agent: data.agent || "Analyzer",
              type: data.type || "analysis",
              content: data.content || data.message || "Agent update",
              confidence: data.confidence || 0.5,
              timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, newMsg]);
          }
        },
        () => {
          setIsConnected(false);
        }
      );

      wsRef.current = ws;

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    } catch (err) {
      console.error("Failed to connect WebSocket:", err);
      setIsConnected(false);
    }
  }, [marketId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getAgentIcon = (role: AgentRole) => {
    switch (role) {
      case "Analyzer":
        return <BrainCircuit className="w-4 h-4" />;
      case "Trader":
        return <Bot className="w-4 h-4" />;
      case "Judge":
        return <Gavel className="w-4 h-4" />;
    }
  };

  const getAgentColor = (role: AgentRole) => {
    switch (role) {
      case "Analyzer":
        return "text-blue-400 bg-blue-400/10 border-blue-400/20";
      case "Trader":
        return "text-primary bg-primary/10 border-primary/20";
      case "Judge":
        return "text-accent bg-accent/10 border-accent/20";
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-2 border-b border-border">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" /> Live Agent Debate
          </CardTitle>
          <div className="flex items-center gap-2">
            {isLoading && (
              <Badge variant="outline" className="text-primary border-primary">
                <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Analyzing...
              </Badge>
            )}
            {!isLoading && isConnected && (
              <Badge
                variant="outline"
                className="animate-pulse text-primary border-primary"
              >
                Live
              </Badge>
            )}
            {!isLoading && !isConnected && (
              <Badge variant="outline" className="text-muted-foreground">
                Offline
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent
        className="flex-1 overflow-y-auto p-4 space-y-4"
        ref={scrollRef}
      >
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
        {messages.length === 0 && !isLoading && !error && (
          <div className="text-center py-8 text-muted-foreground">
            <p>No agent messages yet.</p>
            <p className="text-xs mt-2">
              Agents will appear here when analysis runs.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col gap-2 p-3 rounded-lg border ${getAgentColor(
              msg.agent
            )}`}
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 font-bold text-sm">
                {getAgentIcon(msg.agent)}
                {msg.agent}
              </div>
              <span className="text-xs opacity-70">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <p className="text-sm leading-relaxed">{msg.content}</p>

            <div className="flex items-center justify-between pt-2 mt-1 border-t border-white/5">
              <div className="flex gap-2">
                {msg.attachments?.map((att, i) => (
                  <Button
                    key={i}
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs gap-1"
                  >
                    <FileText className="w-3 h-3" /> Evidence
                  </Button>
                ))}
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span>Confidence: {(msg.confidence * 100).toFixed(0)}%</span>
                <Button variant="ghost" size="icon" className="h-6 w-6">
                  <Play className="w-3 h-3" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
