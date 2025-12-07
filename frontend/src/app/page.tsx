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
  Shield,
  Zap,
  Search,
  FileText,
  BarChart3,
  CheckCircle2,
  Link as LinkIcon,
  Cloud,
  Code,
  Sparkles,
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
          {[
            {
              category: "Medical",
              question:
                "Will a new CAR-T cell therapy be approved by the FDA for treating solid tumors by December 31, 2025?",
              probability: 65,
              daysRemaining: 45,
              volume: "2.4k GAS",
              gradient: "from-blue-500 to-cyan-500",
            },
            {
              category: "Technology",
              question:
                "Will a quantum computer achieve quantum advantage for a practical real-world problem by June 30, 2026?",
              probability: 42,
              daysRemaining: 180,
              volume: "3.8k GAS",
              gradient: "from-purple-500 to-pink-500",
            },
            {
              category: "Climate",
              question:
                "Will the global average temperature in 2025 exceed the previous record high set in 2023?",
              probability: 88,
              daysRemaining: 320,
              volume: "1.9k GAS",
              gradient: "from-green-500 to-emerald-500",
            },
          ].map((market, i) => (
            <Card
              key={i}
              className="group hover:neon-border transition-all duration-300 cursor-pointer bg-card border-border overflow-hidden"
            >
              <div className={`h-2 bg-gradient-to-r ${market.gradient}`} />
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
                    {market.category}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Ends in {market.daysRemaining}d
                  </span>
                </div>
                <CardTitle className="text-lg leading-tight group-hover:text-primary transition-colors">
                  {market.question}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 mt-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Yes Probability
                    </span>
                    <span className="font-bold text-primary">
                      {market.probability}%
                    </span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary"
                      style={{ width: `${market.probability}%` }}
                    />
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
                      {market.volume} Vol
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
          <h2 className="text-3xl font-bold mb-4">How Noro Works</h2>
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

      {/* AI Agents Showcase */}
      <section className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">
            Powered by SpoonOS AI Agents
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Three specialized AI agents work together to analyze markets,
            research evidence, and make intelligent trading decisions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              name: "Analyzer Agent",
              description:
                "Searches PubMed and arXiv for scientific papers, analyzes evidence, and generates probability predictions with confidence scores.",
              icon: Search,
              color: "text-blue-500",
              bgColor: "bg-blue-500/10",
              features: [
                "PubMed & arXiv integration",
                "Evidence-based analysis",
                "Probability calculations",
                "Confidence scoring",
              ],
            },
            {
              name: "Trader Agent",
              description:
                "Takes analysis results, fetches market data from Neo blockchain, and calculates optimal stakes using Kelly Criterion.",
              icon: BarChart3,
              color: "text-green-500",
              bgColor: "bg-green-500/10",
              features: [
                "Real-time market data",
                "Kelly Criterion optimization",
                "Risk-adjusted positions",
                "Trade recommendations",
              ],
            },
            {
              name: "Judge Agent",
              description:
                "Aggregates multiple analyses for consensus, provides weighted probability estimates, and validates outcomes.",
              icon: Scale,
              color: "text-purple-500",
              bgColor: "bg-purple-500/10",
              features: [
                "Multi-agent consensus",
                "Weighted predictions",
                "Outcome validation",
                "Conflict resolution",
              ],
            },
          ].map((agent, i) => (
            <Card
              key={i}
              className="bg-card/50 border-border hover:border-primary/50 transition-all"
            >
              <CardHeader>
                <div
                  className={`w-12 h-12 rounded-xl ${agent.bgColor} flex items-center justify-center mb-4`}
                >
                  <agent.icon className={`w-6 h-6 ${agent.color}`} />
                </div>
                <CardTitle className="text-xl">{agent.name}</CardTitle>
                <CardDescription className="mt-2">
                  {agent.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {agent.features.map((feature, j) => (
                    <li
                      key={j}
                      className="flex items-center gap-2 text-sm text-muted-foreground"
                    >
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-gradient-to-br from-secondary/20 to-secondary/5 rounded-2xl p-8 md:p-12 border border-border">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Built on Neo Blockchain</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Noro leverages the full Neo ecosystem for decentralized, trustless
            prediction markets.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              name: "Neo N3 Smart Contract",
              description:
                "On-chain market creation, trading, and resolution logic",
              icon: Code,
              color: "text-primary",
            },
            {
              name: "NeoFS Storage",
              description:
                "Decentralized storage for market metadata and agent analyses",
              icon: Cloud,
              color: "text-blue-500",
            },
            {
              name: "Neo Oracle",
              description:
                "Automated market resolution using external data sources",
              icon: Shield,
              color: "text-green-500",
            },
            {
              name: "NeoLine Wallet",
              description: "Seamless wallet integration for transactions",
              icon: Wallet,
              color: "text-purple-500",
            },
          ].map((tech, i) => (
            <Card
              key={i}
              className="bg-card/50 border-border/50 hover:border-primary/50 transition-all"
            >
              <CardContent className="p-6">
                <div
                  className={`w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 ${tech.color}`}
                >
                  <tech.icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold mb-2">{tech.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {tech.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Key Features */}
      <section className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Why Noro?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            The first prediction market platform that combines AI intelligence
            with blockchain transparency.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              title: "AI-Powered Analysis",
              description:
                "SpoonOS agents automatically research scientific papers, analyze evidence, and generate probability predictions. No manual research needed.",
              icon: Sparkles,
              color: "text-purple-500",
            },
            {
              title: "Fully Decentralized",
              description:
                "Built on Neo blockchain with NeoFS storage. Markets are immutable, transparent, and censorship-resistant.",
              icon: LinkIcon,
              color: "text-blue-500",
            },
            {
              title: "Evidence-Based Trading",
              description:
                "Trade recommendations are backed by real scientific research from PubMed and arXiv, not speculation.",
              icon: FileText,
              color: "text-green-500",
            },
            {
              title: "Automated Resolution",
              description:
                "Neo Oracle integration automatically resolves markets when events occur, with Judge agent validation.",
              icon: Zap,
              color: "text-orange-500",
            },
            {
              title: "Real-Time Updates",
              description:
                "WebSocket connections provide live agent activity, market updates, and probability changes in real-time.",
              icon: Activity,
              color: "text-pink-500",
            },
            {
              title: "Risk Management",
              description:
                "Trader agent uses Kelly Criterion to calculate optimal stake sizes, balancing risk and reward.",
              icon: Shield,
              color: "text-cyan-500",
            },
          ].map((feature, i) => (
            <Card
              key={i}
              className="bg-card/50 border-border hover:border-primary/50 transition-all"
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 ${feature.color}`}
                  >
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-2">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Use Cases */}
      <section className="bg-secondary/20 rounded-2xl p-8 md:p-12 border border-border">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Perfect For</h2>
          <p className="text-muted-foreground">
            Scientific prediction markets across multiple domains
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              category: "Medical Research",
              examples: [
                "FDA drug approvals",
                "Clinical trial outcomes",
                "Treatment efficacy",
                "Disease breakthroughs",
              ],
              icon: Activity,
              color: "text-red-500",
            },
            {
              category: "Technology",
              examples: [
                "Quantum computing milestones",
                "AI breakthroughs",
                "Hardware innovations",
                "Software releases",
              ],
              icon: BrainCircuit,
              color: "text-blue-500",
            },
            {
              category: "Climate Science",
              examples: [
                "Temperature records",
                "Weather patterns",
                "Environmental events",
                "Climate policy impacts",
              ],
              icon: TrendingUp,
              color: "text-green-500",
            },
          ].map((useCase, i) => (
            <Card key={i} className="bg-card/50 border-border">
              <CardHeader>
                <div
                  className={`w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-3 ${useCase.color}`}
                >
                  <useCase.icon className="w-5 h-5" />
                </div>
                <CardTitle>{useCase.category}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {useCase.examples.map((example, j) => (
                    <li
                      key={j}
                      className="flex items-center gap-2 text-sm text-muted-foreground"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                      {example}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Call to Action */}
      <section className="text-center space-y-6 py-12">
        <h2 className="text-4xl font-bold">Ready to Predict the Future?</h2>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Join the decentralized prediction market revolution. Create markets,
          trade with AI insights, and help shape the future of scientific
          forecasting.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/markets">
            <Button
              size="lg"
              className="h-12 px-8 font-bold bg-primary hover:bg-primary/90 text-black"
            >
              Explore Markets
            </Button>
          </Link>
          <Link href="/create">
            <Button size="lg" variant="outline" className="h-12 px-8 font-bold">
              Create Market
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

function PlusCircleIcon(props: React.SVGProps<SVGSVGElement>) {
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
