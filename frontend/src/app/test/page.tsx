"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  testSimple,
  testContractState,
  testBuyYes,
  testGasTransfer,
  testStorage,
  testInvokeExample,
} from "@/lib/neoline";

export default function TestPage() {
  const [testSimpleResult, setTestSimpleResult] = useState<string>("");
  const [testStateResult, setTestStateResult] = useState<string>("");
  const [testBuyYesResult, setTestBuyYesResult] = useState<string>("");
  const [testStorageResult, setTestStorageResult] = useState<string>("");
  const [testGasResult, setTestGasResult] = useState<string>("");
  const [testExampleResult, setTestExampleResult] = useState<string>("");

  const [marketId, setMarketId] = useState<string>("1");
  const [amount, setAmount] = useState<string>("100000000");
  const [gasAmount, setGasAmount] = useState<string>("1000000");
  const [storageMarketId, setStorageMarketId] = useState<string>("1");

  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const handleTest = async (testName: string, testFn: () => Promise<any>) => {
    setLoading((prev) => ({ ...prev, [testName]: true }));
    try {
      const result = await testFn();
      if (typeof result === "string") {
        return result;
      } else {
        return JSON.stringify(result, null, 2);
      }
    } catch (error: any) {
      return `Error: ${error.message || JSON.stringify(error, null, 2)}`;
    } finally {
      setLoading((prev) => ({ ...prev, [testName]: false }));
    }
  };

  const runTestSimple = async () => {
    const result = await handleTest("simple", testSimple);
    setTestSimpleResult(result);
  };

  const runTestState = async () => {
    const result = await handleTest("state", testContractState);
    setTestStateResult(result);
  };

  const runTestBuyYes = async () => {
    const result = await handleTest("buyYes", () =>
      testBuyYes(marketId, amount)
    );
    setTestBuyYesResult(result);
  };

  const runTestStorage = async () => {
    const result = await handleTest("storage", () =>
      testStorage(storageMarketId)
    );
    setTestStorageResult(result);
  };

  const runTestGas = async () => {
    setLoading((prev) => ({ ...prev, gas: true }));
    try {
      const result = await testGasTransfer(gasAmount);
      setTestGasResult(
        `Success! TXID: ${result.txid || "N/A"}\n${JSON.stringify(
          result,
          null,
          2
        )}`
      );
    } catch (error: any) {
      setTestGasResult(
        `Error: ${error.message || JSON.stringify(error, null, 2)}`
      );
    } finally {
      setLoading((prev) => ({ ...prev, gas: false }));
    }
  };

  const runTestExample = async () => {
    setLoading((prev) => ({ ...prev, example: true }));
    try {
      const result = await testInvokeExample();
      setTestExampleResult(
        `Success!\nTransaction ID: ${result.txid || "N/A"}\nRPC node URL: ${
          result.nodeURL || "N/A"
        }\n\n${JSON.stringify(result, null, 2)}`
      );
    } catch (error: any) {
      let errorMsg = "Error: ";
      if (error.type === "NO_PROVIDER") {
        errorMsg += "No provider available.";
      } else if (error.type === "RPC_ERROR") {
        errorMsg +=
          "There was an error when broadcasting this transaction to the network.";
        if (error.description) {
          errorMsg += `\nDescription: ${error.description}`;
        }
      } else if (error.type === "CANCELED") {
        errorMsg += "The user has canceled this transaction.";
      } else {
        errorMsg += error.message || JSON.stringify(error, null, 2);
      }
      setTestExampleResult(errorMsg);
    } finally {
      setLoading((prev) => ({ ...prev, example: false }));
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6">Contract Test Functions</h1>
      <p className="text-muted-foreground mb-6">
        Test functions to debug contract write operations
      </p>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Test Simple */}
        <Card>
          <CardHeader>
            <CardTitle>1. Test Simple</CardTitle>
            <CardDescription>Basic connectivity test</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={runTestSimple}
              disabled={loading.simple}
              className="w-full"
            >
              {loading.simple ? "Testing..." : "Run Test"}
            </Button>
            {testSimpleResult && (
              <Textarea
                value={testSimpleResult}
                readOnly
                className="min-h-[100px] font-mono text-sm"
              />
            )}
          </CardContent>
        </Card>

        {/* Test Contract State */}
        <Card>
          <CardHeader>
            <CardTitle>2. Test Contract State</CardTitle>
            <CardDescription>Get contract state information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={runTestState}
              disabled={loading.state}
              className="w-full"
            >
              {loading.state ? "Testing..." : "Run Test"}
            </Button>
            {testStateResult && (
              <Textarea
                value={testStateResult}
                readOnly
                className="min-h-[200px] font-mono text-sm whitespace-pre-wrap"
              />
            )}
          </CardContent>
        </Card>

        {/* Test BuyYes */}
        <Card>
          <CardHeader>
            <CardTitle>3. Test BuyYes</CardTitle>
            <CardDescription>
              Test buyYes conditions without executing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="marketId">Market ID</Label>
              <Input
                id="marketId"
                type="text"
                value={marketId}
                onChange={(e) => setMarketId(e.target.value)}
                placeholder="1"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (smallest GAS unit)</Label>
              <Input
                id="amount"
                type="text"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="100000000"
              />
              <p className="text-xs text-muted-foreground">
                100000000 = 1 GAS (8 decimals)
              </p>
            </div>
            <Button
              onClick={runTestBuyYes}
              disabled={loading.buyYes}
              className="w-full"
            >
              {loading.buyYes ? "Testing..." : "Run Test"}
            </Button>
            {testBuyYesResult && (
              <Textarea
                value={testBuyYesResult}
                readOnly
                className="min-h-[300px] font-mono text-sm whitespace-pre-wrap"
              />
            )}
          </CardContent>
        </Card>

        {/* Test Storage */}
        <Card>
          <CardHeader>
            <CardTitle>4. Test Storage</CardTitle>
            <CardDescription>
              Test storage read/write operations
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="storageMarketId">Market ID</Label>
              <Input
                id="storageMarketId"
                type="text"
                value={storageMarketId}
                onChange={(e) => setStorageMarketId(e.target.value)}
                placeholder="1"
              />
            </div>
            <Button
              onClick={runTestStorage}
              disabled={loading.storage}
              className="w-full"
            >
              {loading.storage ? "Testing..." : "Run Test"}
            </Button>
            {testStorageResult && (
              <Textarea
                value={testStorageResult}
                readOnly
                className="min-h-[200px] font-mono text-sm whitespace-pre-wrap"
              />
            )}
          </CardContent>
        </Card>

        {/* Test Gas Transfer */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>5. Test GAS Transfer (Write Function)</CardTitle>
            <CardDescription>
              ⚠️ This actually transfers GAS! Use small amounts only.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="gasAmount">Amount (smallest GAS unit)</Label>
              <Input
                id="gasAmount"
                type="text"
                value={gasAmount}
                onChange={(e) => setGasAmount(e.target.value)}
                placeholder="1000000"
              />
              <p className="text-xs text-muted-foreground">
                1000000 = 0.01 GAS (8 decimals) - Use small amounts for testing!
              </p>
            </div>
            <Button
              onClick={runTestGas}
              disabled={loading.gas}
              variant="destructive"
              className="w-full"
            >
              {loading.gas ? "Transferring..." : "Test GAS Transfer"}
            </Button>
            {testGasResult && (
              <Textarea
                value={testGasResult}
                readOnly
                className="min-h-[150px] font-mono text-sm whitespace-pre-wrap"
              />
            )}
          </CardContent>
        </Card>

        {/* Test Invoke Example (Exact Pattern from Docs) */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>6. Test Invoke (Exact Example Pattern)</CardTitle>
            <CardDescription>
              Test using the exact pattern from NeoLine documentation example.
              This calls testGasTransfer with the exact invoke structure from
              docs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This uses the exact pattern from NeoLine docs:
            </p>
            <pre className="p-3 bg-muted rounded text-xs overflow-x-auto">
              {`neolineN3.invoke({
  scriptHash: '0x...',
  operation: 'testGasTransfer',
  args: [{ type: "Integer", value: "1000000" }],
  fee: '0.0001',
  broadcastOverride: false,
  signers: [{
    account: "...",
    scopes: 16,
    allowedContracts: [...],
    allowedGroups: []
  }]
})`}
            </pre>
            <Button
              onClick={runTestExample}
              disabled={loading.example}
              variant="default"
              className="w-full"
            >
              {loading.example ? "Testing..." : "Test Invoke (Example Pattern)"}
            </Button>
            {testExampleResult && (
              <Textarea
                value={testExampleResult}
                readOnly
                className="min-h-[200px] font-mono text-sm whitespace-pre-wrap"
              />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 p-4 bg-muted rounded-lg">
        <h2 className="font-semibold mb-2">Testing Workflow:</h2>
        <ol className="list-decimal list-inside space-y-1 text-sm">
          <li>
            Run <strong>Test Simple</strong> to verify contract is accessible
          </li>
          <li>
            Run <strong>Test Contract State</strong> to see contract information
          </li>
          <li>
            Run <strong>Test BuyYes</strong> with a market ID to see what
            conditions pass/fail
          </li>
          <li>
            Run <strong>Test Storage</strong> to verify storage operations
          </li>
          <li>
            Optionally run <strong>Test GAS Transfer</strong> with a small
            amount
          </li>
        </ol>
      </div>
    </div>
  );
}
