"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Settings,
  Wallet,
  Network,
  Server,
  FileCode,
  Copy,
  Check,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import {
  getNeoLine,
  isNeoLineAvailable,
  waitForNeoLine,
  type AccountInfo,
  type BalanceResponse,
  NORO_CONTRACT_HASH,
} from "@/lib/neoline";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SettingsPage() {
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [walletBalance, setWalletBalance] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isNeoLineReady, setIsNeoLineReady] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState(API_BASE);
  const [network, setNetwork] = useState<"testnet" | "mainnet">("testnet");

  // Check wallet connection
  useEffect(() => {
    const checkWallet = async () => {
      try {
        if (isNeoLineAvailable()) {
          setIsNeoLineReady(true);
          const neoline = await getNeoLine();
          const account = await neoline.getAccount();
          if (account) {
            setWalletAddress(account.address);
            setIsConnected(true);
            updateBalance(account.address);
          }
        } else {
          await waitForNeoLine();
          setIsNeoLineReady(true);
        }
      } catch (err) {
        console.error("Wallet check failed:", err);
        setIsNeoLineReady(false);
      }
    };

    checkWallet();

    // Listen for account changes
    const handleAccountChanged = (event: CustomEvent) => {
      const account = event.detail as AccountInfo;
      setWalletAddress(account.address);
      setIsConnected(true);
      updateBalance(account.address);
    };

    const handleDisconnected = () => {
      setIsConnected(false);
      setWalletAddress(null);
      setWalletBalance(null);
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

  const updateBalance = async (address: string) => {
    try {
      const neoline = await getNeoLine();
      const balances = await neoline.getBalance();
      if (balances && balances[address]) {
        const addressBalances = balances[address];
        const gasBalance = addressBalances.find(
          (b: BalanceResponse) => b.symbol === "GAS"
        );
        if (gasBalance) {
          const gasAmount = parseFloat(gasBalance.amount);
          setWalletBalance(`${gasAmount.toFixed(4)} GAS`);
        } else {
          setWalletBalance("0 GAS");
        }
      }
    } catch (err) {
      console.error("Failed to update balance:", err);
    }
  };

  const handleConnect = async () => {
    try {
      const neoline = await getNeoLine();
      const account = await neoline.getAccount();
      if (account) {
        setWalletAddress(account.address);
        setIsConnected(true);
        updateBalance(account.address);
      }
    } catch (err) {
      console.error("Failed to connect wallet:", err);
    }
  };

  const handleDisconnect = async () => {
    try {
      const neoline = await getNeoLine();
      await neoline.disconnect();
      setIsConnected(false);
      setWalletAddress(null);
      setWalletBalance(null);
    } catch (err) {
      console.error("Failed to disconnect:", err);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const formatAddress = (address: string) => {
    if (!address) return "";
    return `${address.slice(0, 8)}...${address.slice(-8)}`;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="w-8 h-8" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage your wallet, network, and application preferences.
        </p>
      </div>

      {/* Wallet Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Wallet Connection
          </CardTitle>
          <CardDescription>
            Connect and manage your Neo N3 wallet
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isConnected && walletAddress ? (
            <>
              <div className="space-y-2">
                <Label>Connected Address</Label>
                <div className="flex items-center gap-2">
                  <Input
                    value={walletAddress}
                    readOnly
                    className="font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(walletAddress, "address")}
                  >
                    {copied === "address" ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Balance</Label>
                <div className="flex items-center gap-2">
                  <Input
                    value={walletBalance || "Loading..."}
                    readOnly
                    className="font-mono"
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() =>
                      walletAddress && updateBalance(walletAddress)
                    }
                  >
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              <Button variant="destructive" onClick={handleDisconnect}>
                Disconnect Wallet
              </Button>
            </>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                {isNeoLineReady
                  ? "Connect your NeoLine wallet to get started"
                  : "NeoLine wallet extension not detected. Please install NeoLine to connect."}
              </p>
              <Button
                onClick={handleConnect}
                disabled={!isNeoLineReady}
                className="gap-2"
              >
                <Wallet className="w-4 h-4" />
                Connect Wallet
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Network Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Network Configuration
          </CardTitle>
          <CardDescription>
            Configure blockchain network settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Network</Label>
            <div className="flex gap-2">
              <Button
                variant={network === "testnet" ? "default" : "outline"}
                onClick={() => setNetwork("testnet")}
                className="flex-1"
              >
                TestNet
              </Button>
              <Button
                variant={network === "mainnet" ? "default" : "outline"}
                onClick={() => setNetwork("mainnet")}
                className="flex-1"
              >
                MainNet
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Current network: {network === "testnet" ? "TestNet" : "MainNet"}
            </p>
          </div>
          <div className="space-y-2">
            <Label>RPC Endpoint</Label>
            <Input
              value={
                network === "testnet"
                  ? "https://testnet1.neo.coz.io:443"
                  : "https://mainnet1.neo.coz.io:443"
              }
              readOnly
              className="font-mono text-sm"
            />
          </div>
        </CardContent>
      </Card>

      {/* API Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            API Configuration
          </CardTitle>
          <CardDescription>
            Backend API endpoint settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>API Base URL</Label>
            <div className="flex items-center gap-2">
              <Input
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => copyToClipboard(apiUrl, "api")}
              >
                {copied === "api" ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Backend API endpoint for market data and agent services
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              localStorage.setItem("apiUrl", apiUrl);
              window.location.reload();
            }}
          >
            Save API Settings
          </Button>
        </CardContent>
      </Card>

      {/* Contract Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCode className="w-5 h-5" />
            Contract Information
          </CardTitle>
          <CardDescription>
            Smart contract details and links
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Contract Hash</Label>
            <div className="flex items-center gap-2">
              <Input
                value={NORO_CONTRACT_HASH}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() =>
                  copyToClipboard(NORO_CONTRACT_HASH, "contract")
                }
              >
                {copied === "contract" ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => {
                const explorerUrl =
                  network === "testnet"
                    ? `https://testnet.explorer.neo.org/contract/${NORO_CONTRACT_HASH}`
                    : `https://explorer.neo.org/contract/${NORO_CONTRACT_HASH}`;
                window.open(explorerUrl, "_blank");
              }}
            >
              <ExternalLink className="w-4 h-4" />
              View on Explorer
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Application Info */}
      <Card>
        <CardHeader>
          <CardTitle>Application Information</CardTitle>
          <CardDescription>Version and system details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Version</span>
            <span className="text-sm font-mono">0.1.0</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Platform</span>
            <span className="text-sm">Neo N3</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Network</span>
            <span className="text-sm capitalize">{network}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

