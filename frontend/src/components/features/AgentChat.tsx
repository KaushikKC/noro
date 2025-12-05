"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, BrainCircuit, Gavel, Play, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";

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

// Mock initial messages
const INITIAL_MESSAGES: AgentMessage[] = [
  {
    id: "1",
    agent: "Analyzer",
    type: "analysis",
    content: "Reviewed 14 recent papers on CRISPR-Cas9 efficacy in sickle cell trials. Vertex Pharmaceuticals report (DOI: 10.1056/NEJMoa2031054) indicates 95% symptom reduction.",
    confidence: 0.85,
    timestamp: Date.now() - 100000,
    attachments: [{ type: "pdf", neoFsHash: "QmX7..." }]
  },
  {
    id: "2",
    agent: "Trader",
    type: "trade",
    content: "Based on positive analysis signal, increasing probability estimate. Executing BUY YES order for 500 GAS.",
    confidence: 0.92,
    timestamp: Date.now() - 50000,
  }
];

export function AgentChat({ marketId }: { marketId: string }) {
  const [messages, setMessages] = useState<AgentMessage[]>(INITIAL_MESSAGES);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const newMsg: AgentMessage = {
          id: Date.now().toString(),
          agent: Math.random() > 0.5 ? "Analyzer" : "Trader",
          type: "analysis",
          content: "Monitoring new FDA guidance documents. No negative signals detected in latest press release.",
          confidence: 0.88,
          timestamp: Date.now(),
        };
        setMessages(prev => [...prev, newMsg]);
      }
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getAgentIcon = (role: AgentRole) => {
    switch (role) {
      case "Analyzer": return <BrainCircuit className="w-4 h-4" />;
      case "Trader": return <Bot className="w-4 h-4" />;
      case "Judge": return <Gavel className="w-4 h-4" />;
    }
  };

  const getAgentColor = (role: AgentRole) => {
    switch (role) {
      case "Analyzer": return "text-blue-400 bg-blue-400/10 border-blue-400/20";
      case "Trader": return "text-primary bg-primary/10 border-primary/20";
      case "Judge": return "text-accent bg-accent/10 border-accent/20";
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-2 border-b border-border">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" /> Live Agent Debate
          </CardTitle>
          <Badge variant="outline" className="animate-pulse text-primary border-primary">
            Live
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col gap-2 p-3 rounded-lg border ${getAgentColor(msg.agent)}`}>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 font-bold text-sm">
                {getAgentIcon(msg.agent)}
                {msg.agent}
              </div>
              <span className="text-xs opacity-70">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </span>
            </div>
            
            <p className="text-sm leading-relaxed">
              {msg.content}
            </p>
            
            <div className="flex items-center justify-between pt-2 mt-1 border-t border-white/5">
              <div className="flex gap-2">
                {msg.attachments?.map((att, i) => (
                   <Button key={i} variant="ghost" size="sm" className="h-6 px-2 text-xs gap-1">
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

