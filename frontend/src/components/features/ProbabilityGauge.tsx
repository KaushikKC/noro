"use client";

import { Card, CardContent } from "@/components/ui/card";

export function ProbabilityGauge({ probability }: { probability: number }) {
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (probability / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center w-64 h-64 mx-auto">
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx="128"
          cy="128"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="transparent"
          className="text-secondary"
        />
        <circle
          cx="128"
          cy="128"
          r={radius}
          stroke="currentColor"
          strokeWidth="12"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="text-primary transition-all duration-1000 ease-out"
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-bold text-white tracking-tighter">
          {probability}%
        </span>
        <span className="text-sm text-primary font-medium uppercase tracking-widest mt-2">
          Probability
        </span>
      </div>
    </div>
  );
}

