"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Wallet, Loader2 } from "lucide-react";
import {
  getNeoLine,
  isNeoLineAvailable,
  waitForNeoLine,
  type AccountInfo,
  type BalanceResponse,
} from "@/lib/neoline";

export function WalletConnector() {
  const [isConnected, setIsConnected] = useState(false);
  const [address, setAddress] = useState<string | null>(null);
  const [balance, setBalance] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNeoLineReady, setIsNeoLineReady] = useState(false);

  // Check for NeoLine on mount
  useEffect(() => {
    const checkNeoLine = async () => {
      try {
        if (isNeoLineAvailable()) {
          setIsNeoLineReady(true);
        } else {
          // Wait for NeoLine to load
          await waitForNeoLine();
          setIsNeoLineReady(true);
        }
      } catch (err) {
        console.error("NeoLine not available:", err);
        setIsNeoLineReady(false);
      }
    };

    checkNeoLine();

    // Listen for account changes
    const handleAccountChanged = (event: CustomEvent) => {
      const account = event.detail as AccountInfo;
      setAddress(account.address);
      updateBalance(account.address);
    };

    // Listen for disconnection
    const handleDisconnected = () => {
      setIsConnected(false);
      setAddress(null);
      setBalance(null);
    };

    window.addEventListener(
      "NEOLine.N3.EVENT.ACCOUNT_CHANGED",
      handleAccountChanged as EventListener
    );
    window.addEventListener(
      "NEOLine.N3.EVENT.DISCONNECTED",
      handleDisconnected
    );

    return () => {
      window.removeEventListener(
        "NEOLine.N3.EVENT.ACCOUNT_CHANGED",
        handleAccountChanged as EventListener
      );
      window.removeEventListener(
        "NEOLine.N3.EVENT.DISCONNECTED",
        handleDisconnected
      );
    };
  }, []);

  const updateBalance = async (accountAddress: string) => {
    try {
      const neoline = await getNeoLine();
      const balances = await neoline.getBalance();

      // getBalance() returns an object with address as key and array of balances as value
      // Format: { "address": [{symbol, amount, contract}, ...] }
      if (balances && balances[accountAddress]) {
        const addressBalances = balances[accountAddress];
        const gasBalance = addressBalances.find(
          (b: BalanceResponse) => b.symbol === "GAS"
        );
        if (gasBalance) {
          // Amount is already in the correct format (string like "10063.4476161")
          // No need to divide - it's already in GAS units
          const gasAmount = parseFloat(gasBalance.amount);
          setBalance(`${gasAmount.toFixed(4)} GAS`);
        } else {
          setBalance("0 GAS");
        }
      } else {
        // Try to find balance in any address if accountAddress key doesn't match exactly
        const addresses = Object.keys(balances || {});
        if (addresses.length > 0) {
          const firstAddress = addresses[0];
          const addressBalances = balances[firstAddress];
          const gasBalance = addressBalances.find(
            (b: BalanceResponse) => b.symbol === "GAS"
          );
          if (gasBalance) {
            const gasAmount = parseFloat(gasBalance.amount);
            setBalance(`${gasAmount.toFixed(4)} GAS`);
          } else {
            setBalance("0 GAS");
          }
        } else {
          setBalance("0 GAS");
        }
      }
    } catch (err) {
      console.error("Failed to get balance:", err);
      setBalance("N/A");
    }
  };

  const connect = async () => {
    setIsLoading(true);
    setError(null);

    try {
      if (!isNeoLineReady) {
        await waitForNeoLine();
        setIsNeoLineReady(true);
      }

      const neoline = await getNeoLine();
      const account = await neoline.getAccount();

      setAddress(account.address);
      setIsConnected(true);
      await updateBalance(account.address);

      // Listen for account changes
      neoline.addEventListener(
        "NEOLine.N3.EVENT.ACCOUNT_CHANGED",
        (data: AccountInfo) => {
          setAddress(data.address);
          updateBalance(data.address);
        }
      );

      // Listen for disconnection
      neoline.addEventListener("NEOLine.N3.EVENT.DISCONNECTED", () => {
        setIsConnected(false);
        setAddress(null);
        setBalance(null);
      });
    } catch (err) {
      console.error("Connection error:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to connect to NeoLine";
      setError(errorMessage);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  const disconnect = () => {
    setIsConnected(false);
    setAddress(null);
    setBalance(null);
    setError(null);
  };

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address);
      // You could add a toast notification here
    }
  };

  if (isConnected && address) {
    const truncatedAddress = `${address.slice(0, 6)}...${address.slice(-4)}`;

    return (
      <div className="flex items-center gap-4 bg-secondary/50 px-4 py-2 rounded-full border border-border">
        <div className="flex flex-col items-end">
          <button
            onClick={copyAddress}
            className="text-xs text-muted-foreground font-mono hover:text-foreground transition-colors cursor-pointer"
            title="Click to copy address"
          >
            {truncatedAddress}
          </button>
          <span className="text-sm font-bold text-primary neon-text">
            {balance || "Loading..."}
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={disconnect}
          className="text-destructive hover:text-destructive/80 hover:bg-destructive/10 h-8 px-2"
        >
          Disconnect
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <Button
        onClick={connect}
        disabled={isLoading || !isNeoLineReady}
        className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 font-bold"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Connecting...
          </>
        ) : (
          <>
            <Wallet className="w-4 h-4" />
            Connect NeoLine
          </>
        )}
      </Button>
      {error && <span className="text-xs text-destructive">{error}</span>}
      {!isNeoLineReady && !error && (
        <span className="text-xs text-muted-foreground">
          NeoLine wallet not detected
        </span>
      )}
    </div>
  );
}
