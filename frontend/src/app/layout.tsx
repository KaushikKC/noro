import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn } from "@/lib/utils";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "noro | Scientific Prediction Markets",
  description:
    "Decentralized scientific prediction markets powered by SpoonOS agents on Neo N3.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* NeoLine N3 dAPI Script */}
        <script
          src="https://cdn.jsdelivr.net/npm/@neoline/neoline-dapi@latest/lib/browser.js"
          async
        />
      </head>
      <body
        className={cn(
          geistSans.variable,
          geistMono.variable,
          "antialiased min-h-screen bg-background font-sans"
        )}
      >
        <Navbar />
        <Sidebar />

        <main className="pt-20 md:pl-64 min-h-screen transition-all duration-300">
          <div className="container mx-auto px-4 py-6 max-w-7xl">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
