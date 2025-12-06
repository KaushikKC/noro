"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { buyYes, buyNo, getNeoLine } from "@/lib/neoline";

interface TradePanelProps {
  marketId: string;
}

export function TradePanel({ marketId }: TradePanelProps) {
  const [amount, setAmount] = useState("1");
  const [outcome, setOutcome] = useState<"Yes" | "No">("Yes");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleTrade = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Check if NeoLine is connected
      const neoline = await getNeoLine();
      await neoline.getAccount(); // This will throw if not connected

      // Convert amount to smallest unit (GAS has 8 decimals)
      const amountSmallest = Math.floor(
        parseFloat(amount) * 100000000
      ).toString();

      // Call buyYes or buyNo
      const result =
        outcome === "Yes"
          ? await buyYes(marketId, amountSmallest)
          : await buyNo(marketId, amountSmallest);

      if (result.txid) {
        setSuccess(`Transaction submitted! TXID: ${result.txid}`);
      } else {
        setSuccess("Transaction submitted successfully!");
      }
    } catch (err: any) {
      console.error("Trade error:", err);
      console.error("Error details:", err);

      // Extract more detailed error message
      let errorMessage = "Failed to execute trade.";
      if (err.type) {
        switch (err.type) {
          case "NO_PROVIDER":
            errorMessage =
              "NeoLine wallet not detected. Please install NeoLine extension.";
            break;
          case "RPC_ERROR":
            errorMessage = `RPC Error: ${
              err.description ||
              err.message ||
              "Network connection failed. Please check your network and try again."
            }`;
            break;
          case "CANCELED":
            errorMessage = "Transaction was canceled.";
            break;
          default:
            errorMessage =
              err.description || err.message || "Unknown error occurred.";
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-primary/20 sticky top-24">
      <CardHeader>
        <CardTitle>Trade</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <Button
            variant={outcome === "Yes" ? "default" : "outline"}
            onClick={() => setOutcome("Yes")}
            className={`h-20 flex flex-col gap-1 ${
              outcome === "Yes"
                ? "bg-primary text-black hover:bg-primary/90"
                : ""
            }`}
          >
            <span className="text-lg font-bold">YES</span>
            <span className="text-xs opacity-80 flex items-center gap-1">
              <ArrowUpRight className="w-3 h-3" /> $0.78
            </span>
          </Button>
          <Button
            variant={outcome === "No" ? "destructive" : "outline"}
            onClick={() => setOutcome("No")}
            className={`h-20 flex flex-col gap-1 ${
              outcome === "No"
                ? "bg-destructive text-white hover:bg-destructive/90"
                : ""
            }`}
          >
            <span className="text-lg font-bold">NO</span>
            <span className="text-xs opacity-80 flex items-center gap-1">
              <ArrowDownRight className="w-3 h-3" /> $0.22
            </span>
          </Button>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Amount (GAS)</label>
          <div className="relative">
            <Input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="pl-4 pr-16 h-12 text-lg font-bold"
            />
            <span className="absolute right-4 top-3 text-sm text-muted-foreground font-mono">
              GAS
            </span>
          </div>
        </div>

        <div className="p-4 bg-secondary/30 rounded-lg space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Est. Shares</span>
            <span className="font-mono">12.8</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Potential Return</span>
            <span className="font-mono text-primary">+28%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Fees</span>
            <span className="font-mono">0.01 GAS</span>
          </div>
        </div>

        <Button
          className="w-full h-12 text-lg font-bold gap-2"
          size="lg"
          onClick={handleTrade}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing...
            </>
          ) : (
            `Buy ${outcome}`
          )}
        </Button>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg text-sm text-green-500">
            {success}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-amber-500 justify-center">
          <AlertTriangle className="w-3 h-3" />
          <span>Transactions are final on Neo TestNet</span>
        </div>
      </CardContent>
    </Card>
  );
}
