"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, Database, AlertCircle, CheckCircle } from "lucide-react";

export default function OraclePage() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Oracle Admin</h1>
          <p className="text-muted-foreground">Manage and monitor data resolution requests.</p>
        </div>
        <Button className="gap-2 bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20 border">
          <AlertCircle className="w-4 h-4" /> Emergency Pause
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="bg-card/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Resolved (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">12</div>
          </CardContent>
        </Card>
        <Card className="bg-card/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">0</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" /> Request Queue
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 border border-border rounded-lg bg-secondary/5">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-muted-foreground">REQ-{1000+i}</span>
                    <Badge variant="outline" className="text-yellow-500 border-yellow-500/20 bg-yellow-500/10">
                      Pending
                    </Badge>
                  </div>
                  <p className="font-medium">Market: Will SpaceX launch Starship...?</p>
                  <p className="text-xs text-muted-foreground">Source: NOAA Webhook • ID: 0x92...8s9d</p>
                </div>
                <div className="flex gap-2 mt-4 md:mt-0">
                   <Button size="sm" variant="outline" className="gap-2">
                     View Logs
                   </Button>
                   <Button size="sm" className="gap-2 bg-primary text-black">
                     <ShieldCheck className="w-4 h-4" /> Trigger Resolution
                   </Button>
                </div>
              </div>
            ))}
            
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 border border-border rounded-lg bg-secondary/5 opacity-60">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm text-muted-foreground">REQ-0998</span>
                    <Badge variant="outline" className="text-green-500 border-green-500/20 bg-green-500/10">
                      Success
                    </Badge>
                  </div>
                  <p className="font-medium">Market: Will Bitcoin pass $100k...?</p>
                  <p className="text-xs text-muted-foreground">Source: CoinGecko • ID: 0x12...3d4f</p>
                </div>
                <div className="flex gap-2 mt-4 md:mt-0">
                   <Button size="sm" variant="ghost" disabled>
                     <CheckCircle className="w-4 h-4 mr-2" /> Resolved
                   </Button>
                </div>
              </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

