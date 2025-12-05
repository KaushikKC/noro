"use client";

import Link from "next/link";
import { WalletConnector } from "@/components/features/WalletConnector";
import { Button } from "@/components/ui/button";
import { PlayCircle, Plus } from "lucide-react";

export function Navbar() {
  return (
    <nav className="h-16 fixed top-0 left-0 right-0 z-40 glass border-b border-border/50 px-6 flex items-center justify-between">
      <div className="flex items-center gap-12">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center font-bold text-black text-xl">
            X
          </div>
          <span className="text-xl font-bold tracking-tight">PredictX</span>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground gap-2 hidden sm:flex"
        >
          <PlayCircle className="w-4 h-4" />
          Watch Demo
        </Button>

        <Link href="/create">
          <Button
            size="sm"
            className="gap-2 bg-accent hover:bg-accent/90 text-white hidden sm:flex"
          >
            <Plus className="w-4 h-4" />
            Create Market
          </Button>
        </Link>

        <WalletConnector />
      </div>
    </nav>
  );
}
