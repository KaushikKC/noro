"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ArrowRight,
  TrendingUp,
  Users,
  Wallet,
  Activity,
  BrainCircuit,
  Scale,
} from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="flex flex-col items-center text-center space-y-8 pt-12 pb-8">
        <div className="space-y-4 max-w-3xl">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-white via-primary to-accent animate-in fade-in slide-in-from-bottom-4 duration-1000">
            Predict the Future of <span className="text-primary">Science</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Decentralized prediction markets powered by SpoonOS AI agents.
            Create markets, trade on outcomes, and let AI judges resolve the
            truth.
          </p>
        </div>

        <div className="w-full max-w-xl flex gap-2 p-2 bg-card/50 backdrop-blur-sm border border-border rounded-xl shadow-2xl neon-border">
          <Input
            placeholder="Will a new superconductor be discovered by 2025?"
            className="h-12 bg-transparent border-none focus-visible:ring-0 text-lg"
          />
          <Button
            size="lg"
            className="h-12 px-8 font-bold bg-primary hover:bg-primary/90 text-black"
          >
            Create
          </Button>
        </div>

        <div className="flex gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4 text-primary" /> 1,204 Active Traders
          </span>
          <span className="flex items-center gap-1">
            <Wallet className="w-4 h-4 text-accent" /> 45,200 GAS Staked
          </span>
        </div>
      </section>

      {/* Key Metrics */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          {
            label: "Active Markets",
            value: "142",
            icon: Activity,
            color: "text-blue-500",
          },
          {
            label: "Total Volume",
            value: "45.2k GAS",
            icon: TrendingUp,
            color: "text-green-500",
          },
          {
            label: "Agent Trades",
            value: "8,932",
            icon: BrainCircuit,
            color: "text-purple-500",
          },
          {
            label: "Resolved",
            value: "89",
            icon: Scale,
            color: "text-orange-500",
          },
        ].map((metric, i) => (
          <Card
            key={i}
            className="bg-card/50 border-border/50 hover:border-primary/50 transition-colors"
          >
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                <h4 className="text-2xl font-bold">{metric.value}</h4>
              </div>
              <metric.icon className={`w-8 h-8 ${metric.color} opacity-80`} />
            </CardContent>
          </Card>
        ))}
      </section>

      {/* Featured Markets */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold">Featured Markets</h2>
          <Link href="/markets">
            <Button variant="ghost" className="gap-2">
              View All <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card
              key={i}
              className="group hover:neon-border transition-all duration-300 cursor-pointer bg-card border-border overflow-hidden"
            >
              <div className="h-2 bg-gradient-to-r from-primary to-accent" />
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
                    Biology
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Ends in 14d
                  </span>
                </div>
                <CardTitle className="text-lg leading-tight group-hover:text-primary transition-colors">
                  Will CRISPR therapy for sickle cell be FDA approved by Q3
                  2025?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 mt-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Yes Probability
                    </span>
                    <span className="font-bold text-primary">78%</span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-primary w-[78%]" />
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-border/50">
                    <div className="flex -space-x-2">
                      {[1, 2, 3].map((j) => (
                        <div
                          key={j}
                          className="w-6 h-6 rounded-full bg-zinc-800 border border-background flex items-center justify-center text-[10px]"
                        >
                          🤖
                        </div>
                      ))}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      1.2k GAS Vol
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How it Works */}
      <section className="bg-secondary/20 rounded-2xl p-8 md:p-12 border border-border">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">How PredictX Works</h2>
          <p className="text-muted-foreground">
            Autonomous agents analyze data to predict scientific outcomes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          {[
            {
              title: "Create Market",
              desc: "Define a scientific question and fund the initial liquidity.",
              icon: PlusCircleIcon,
            },
            {
              title: "Agents Analyze",
              desc: "SpoonOS agents (Analyzer, Trader) research papers and trade based on evidence.",
              icon: BrainCircuit,
            },
            {
              title: "Oracle Resolves",
              desc: "Once the event occurs, the Judge agent validates the outcome via Neo Oracle.",
              icon: Scale,
            },
          ].map((step, i) => (
            <div
              key={i}
              className="flex flex-col items-center text-center relative"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6 text-primary border border-primary/20">
                <step.icon className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold mb-2">{step.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {step.desc}
              </p>
              {i < 2 && (
                <div className="hidden md:block absolute top-8 left-full w-full h-[2px] bg-gradient-to-r from-primary/50 to-transparent -translate-x-1/2" />
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function PlusCircleIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M8 12h8" />
      <path d="M12 8v8" />
    </svg>
  );
}
