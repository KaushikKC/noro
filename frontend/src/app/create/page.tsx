"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Info, Link as LinkIcon, Loader2 } from "lucide-react";
import {
  createMarket as createMarketContract,
  isNeoLineAvailable,
} from "@/lib/neoline";
import { useRouter } from "next/navigation";

export default function CreateMarketPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    question: "",
    description: "",
    category: "Biology",
    resolveDate: "",
    oracle: "https://api.example.com/oracle",
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreate = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    // Validate form
    if (!formData.question.trim()) {
      setError("Question is required");
      setIsLoading(false);
      return;
    }
    if (!formData.description.trim()) {
      setError("Description is required");
      setIsLoading(false);
      return;
    }
    if (!formData.resolveDate) {
      setError("Resolution date is required");
      setIsLoading(false);
      return;
    }

    try {
      // Check if NeoLine is available
      if (!isNeoLineAvailable()) {
        setError(
          "NeoLine wallet extension is not installed or not available. Please install NeoLine wallet extension."
        );
        setIsLoading(false);
        return;
      }

      console.log(
        "✅ NeoLine is available, proceeding with market creation..."
      );

      // Convert date to Unix timestamp in milliseconds
      // HTML date input gives "YYYY-MM-DD" format
      // We need to set it to end of day (23:59:59) in UTC to ensure it's in the future
      const dateInput = formData.resolveDate; // Format: "YYYY-MM-DD"
      const dateObj = new Date(dateInput + "T23:59:59.999Z"); // Set to end of day UTC
      const resolveDate = dateObj.getTime().toString();

      // Validate date is in the future
      const now = Date.now();
      if (dateObj.getTime() <= now) {
        setError("Resolution date must be in the future");
        setIsLoading(false);
        return;
      }

      console.log("Date conversion:", {
        input: dateInput,
        dateObj: dateObj.toISOString(),
        timestamp: resolveDate,
        now: now,
        isValid: dateObj.getTime() > now,
      });

      // Use createMarketContract function which handles:
      // - Address conversion (Base58 to script hash)
      // - Global scope
      // - Proper signers configuration
      console.log("Calling createMarketContract with:", {
        question: formData.question,
        description: formData.description,
        category: formData.category,
        resolveDate: resolveDate,
        oracleUrl: formData.oracle,
      });

      console.log(
        "⏳ About to call createMarketContract - wallet popup should appear now..."
      );
      const invokeResult = await createMarketContract(
        formData.question,
        formData.description,
        formData.category,
        resolveDate,
        formData.oracle
      );
      console.log("✅ createMarketContract completed:", invokeResult);

      if (invokeResult.txid) {
        setSuccess(
          `Market created! Transaction: ${invokeResult.txid}. Market data stored in NeoFS.`
        );
        // Redirect to markets page after 2 seconds
        setTimeout(() => {
          router.push("/markets");
        }, 2000);
      } else {
        setSuccess(
          "Market transaction prepared. Please confirm in NeoLine wallet."
        );
      }
    } catch (err) {
      console.error("Create market error:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to create market. Please check your wallet connection.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Create a Scientific Market</h1>
        <p className="text-muted-foreground">
          Define a verifiable scientific question for agents to analyze.
        </p>
      </div>

      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle>Market Details</CardTitle>
          <CardDescription>
            Provide clear criteria for resolution.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium">Question</label>
            <Input
              name="question"
              placeholder="e.g. Will treatment X be approved by 2026?"
              value={formData.question}
              onChange={handleChange}
              className="text-lg"
            />
            <p className="text-xs text-muted-foreground">
              Must be a Yes/No question resolvable by scientific evidence.
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Description & Evidence Criteria
            </label>
            <Textarea
              name="description"
              placeholder="Provide details on what constitutes a 'Yes' outcome. Link specific journals or databases."
              value={formData.description}
              onChange={handleChange}
              rows={5}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <select
                name="category"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formData.category}
                onChange={handleChange}
              >
                <option value="Biology">Biology</option>
                <option value="Climate">Climate</option>
                <option value="Physics">Physics</option>
                <option value="Chemistry">Chemistry</option>
                <option value="Others">Others</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Resolution Date</label>
              <Input
                type="date"
                name="resolveDate"
                value={formData.resolveDate}
                onChange={handleChange}
                min={new Date().toISOString().split("T")[0]} // Prevent selecting past dates
              />
              <p className="text-xs text-muted-foreground">
                Date must be in the future. Will be set to end of day (23:59:59
                UTC).
              </p>
            </div>
          </div>

          <div className="space-y-2 pt-4 border-t border-border">
            <label className="text-sm font-medium flex items-center gap-2">
              Oracle URL
              <LinkIcon className="w-3 h-3 text-muted-foreground" />
            </label>
            <Input
              name="oracle"
              placeholder="https://api.example.com/oracle"
              value={formData.oracle}
              onChange={handleChange}
            />
            <p className="text-xs text-muted-foreground">
              URL for oracle to fetch resolution data
            </p>
          </div>

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

          <div className="pt-6 flex justify-end gap-4">
            <Button
              variant="ghost"
              onClick={() => router.push("/markets")}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              className="bg-primary text-black font-bold min-w-[150px]"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Creating...
                </>
              ) : (
                "Create Market"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg text-sm text-blue-200 flex gap-3">
        <Info className="w-5 h-5 flex-shrink-0" />
        <div>
          <p className="font-bold">Cost Estimate</p>
          <p>
            Creating a market requires a deposit of 10 GAS. This will be
            refunded if the market resolves successfully without dispute.
          </p>
        </div>
      </div>
    </div>
  );
}
