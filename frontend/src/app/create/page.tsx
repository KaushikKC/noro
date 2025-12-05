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
import { Calendar, Info, Link as LinkIcon } from "lucide-react";

export default function CreateMarketPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    question: "",
    description: "",
    category: "Biology",
    resolveDate: "",
    oracle: "pubmed",
    liquidity: "5",
  });

  const handleChange = (e: any) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreate = () => {
    // Logic to trigger wallet sign
    alert(JSON.stringify(formData, null, 2));
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
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-border">
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                Initial Liquidity (GAS)
                <Info className="w-3 h-3 text-muted-foreground" />
              </label>
              <Input
                type="number"
                name="liquidity"
                value={formData.liquidity}
                onChange={handleChange}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                Oracle Source
                <LinkIcon className="w-3 h-3 text-muted-foreground" />
              </label>
              <select
                name="oracle"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={formData.oracle}
                onChange={handleChange}
              >
                <option value="pubmed">PubMed / Scientific Journals</option>
                <option value="noaa">NOAA (Climate)</option>
                <option value="custom">Custom Webhook (Demo)</option>
              </select>
            </div>
          </div>

          <div className="pt-6 flex justify-end gap-4">
            <Button variant="ghost">Cancel</Button>
            <Button
              onClick={handleCreate}
              className="bg-primary text-black font-bold min-w-[150px]"
            >
              Create Market
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
