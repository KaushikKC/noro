"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bot, Search, FileJson, Download } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export default function AgentsPage() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Agent Console</h1>
          <p className="text-muted-foreground">
            Monitor SpoonOS agent activities and decision logic.
          </p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="w-4 h-4" /> Export All Logs
        </Button>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="Search logs by content or agent ID..."
          className="max-w-md"
        />
        <Button variant="secondary">Filter</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" /> Recent Activities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="flex flex-col gap-2 p-4 border border-border rounded-lg hover:bg-secondary/10 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <Badge variant={i % 2 === 0 ? "default" : "secondary"}>
                      {i % 2 === 0 ? "Analyzer" : "Trader"}
                    </Badge>
                    <span className="text-sm text-muted-foreground font-mono">
                      0x71...9a2b
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    2 mins ago
                  </span>
                </div>
                <p className="text-sm mt-1">
                  {i % 2 === 0
                    ? "Analyzed 15 PDF documents from PubMed regarding CRISPR efficacy."
                    : "Executed trade proposal for Market #124 based on confidence threshold > 0.8."}
                </p>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileJson className="w-3 h-3" /> View JSON
                  </span>
                  <span className="font-mono text-primary">
                    Gas Used: 0.0012
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
