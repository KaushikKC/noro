"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Store,
  PlusCircle,
  Bot,
  ShieldCheck,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Markets", href: "/markets", icon: Store },
  { name: "Create Market", href: "/create", icon: PlusCircle },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "Oracle", href: "/oracle", icon: ShieldCheck },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-card border-r border-border fixed left-0 top-0 pt-20 pb-4 flex flex-col z-30 hidden md:flex">
      <div className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors",
                isActive
                  ? "bg-primary/10 text-primary border-l-2 border-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <item.icon
                className={cn("w-5 h-5", isActive && "text-primary")}
              />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </div>

      <div className="px-6 py-4 border-t border-border">
        <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
          <p className="text-xs font-medium text-accent mb-1">
            Running on Neo TestNet
          </p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-muted-foreground">
              Block: 8,123,442
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
