/**
 * NeoLine N3 dAPI Integration
 * Based on: https://neoline.io/dapi/N3.html
 *
 * This module provides API-based integration with NeoLine wallet
 * No SDK - using direct API calls as per requirements
 */

// import { rpc } from "viem/utils";
import { rpc } from "@cityofzion/neon-js";
import { wallet } from "@cityofzion/neon-core";

// Type definitions based on NeoLine dAPI documentation
interface NeoLineProvider {
  name: string;
  website: string;
  version: string;
  compatibility: string[];
  extra: Record<string, any>;
}

interface AccountInfo {
  address: string; // Base58 address
  label?: string;
  scriptHash?: string; // Script hash (hex without 0x)
}

interface BalanceResponse {
  contract: string;
  symbol: string;
  amount: string;
}

interface NetworkInfo {
  networks: string[];
  chainId: number;
  defaultNetwork: string;
}

interface TransactionData {
  scriptHash: string;
  operation: string;
  args: Array<{
    type: string;
    value: any;
  }>;
  fee?: string;
  extraSystemFee?: string;
  overrideSystemFee?: string;
  broadcastOverride?: boolean;
  signers?: Array<{
    account: string;
    scopes: number;
    allowedContracts?: string[];
    allowedGroups?: string[];
  }>;
}

interface InvokeResult {
  script: string;
  state: string;
  gasconsumed: string;
  stack: Array<{
    type: string;
    value: any;
  }>;
  txid?: string;
}

// Declare global types for window
declare global {
  interface Window {
    NEOLineN3?: {
      Init: new () => {
        getProvider: () => NeoLineProvider;
        getAccount: () => Promise<AccountInfo>;
        getPublicKey: () => Promise<string>;
        getBalance: () => Promise<Record<string, BalanceResponse[]>>;
        getNetworks: () => Promise<NetworkInfo>;
        invokeRead: (params: any) => Promise<InvokeResult>;
        invoke: (params: any) => Promise<InvokeResult>;
        signMessage: (params: { message: string }) => Promise<string>;
        addEventListener: (
          event: string,
          callback: (data: any) => void
        ) => void;
        removeEventListener: (
          event: string,
          callback: (data: any) => void
        ) => void;
      };
    };
    NEOLine?: {
      Init: new () => any;
    };
  }
}

class NeoLineN3 {
  private provider: any = null; // NeoLine provider instance

  // Expose provider for direct access (for testing)
  public get _provider() {
    return this.provider;
  }

  constructor() {
    // Check if NeoLine is available
    if (typeof window === "undefined") {
      throw new Error("NeoLine dAPI is only available in browser environment");
    }
  }

  /**
   * Initialize NeoLine dAPI
   * Waits for NEOLine.N3.EVENT.READY event
   */
  async init(): Promise<NeoLineN3> {
    return new Promise((resolve, reject) => {
      if (window.NEOLineN3) {
        try {
          // Init() is a class constructor, must be called with 'new'
          this.provider = new window.NEOLineN3.Init();
          console.log("RPC", this.provider);
          if (this.provider) {
            resolve(this);
          } else {
            reject(new Error("NeoLine N3 dAPI failed to initialize"));
          }
        } catch (error) {
          reject(error);
        }
      } else {
        // Wait for READY event
        const readyHandler = () => {
          try {
            // Init() is a class constructor, must be called with 'new'
            this.provider = new window.NEOLineN3!.Init();
            if (this.provider) {
              window.removeEventListener(
                "NEOLine.N3.EVENT.READY",
                readyHandler
              );
              resolve(this);
            } else {
              reject(new Error("NeoLine N3 dAPI failed to initialize"));
            }
          } catch (error) {
            window.removeEventListener("NEOLine.N3.EVENT.READY", readyHandler);
            reject(error);
          }
        };

        window.addEventListener("NEOLine.N3.EVENT.READY", readyHandler);

        // Timeout after 10 seconds
        setTimeout(() => {
          window.removeEventListener("NEOLine.N3.EVENT.READY", readyHandler);
          reject(new Error("NeoLine N3 dAPI timeout - wallet not detected"));
        }, 10000);
      }
    });
  }

  /**
   * Get provider information
   */
  async getProvider(): Promise<NeoLineProvider> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.getProvider();
  }

  /**
   * Get connected account
   */
  async getAccount(): Promise<AccountInfo> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    const account = await this.provider.getAccount();

    // Try to get script hash if available from provider
    // Some NeoLine versions might provide it
    if (!account.scriptHash && this.provider.getScriptHash) {
      try {
        account.scriptHash = await this.provider.getScriptHash();
      } catch (e) {
        // Ignore if not available
      }
    }

    return account;
  }

  /**
   * Get script hash from Base58 address (if provider supports it)
   */
  async getScriptHashFromAddress(address: string): Promise<string | null> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }

    // Try NeoLine's addressToScriptHash if available
    if (this.provider.addressToScriptHash) {
      try {
        const result = await this.provider.addressToScriptHash({ address });
        return result.scriptHash || null;
      } catch (e) {
        console.log("addressToScriptHash not available:", e);
      }
    }

    return null;
  }

  /**
   * Get public key
   */
  async getPublicKey(): Promise<string> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.getPublicKey();
  }

  /**
   * Get balance for connected account
   * According to NeoLine dAPI docs, getBalance() is called without parameters
   * and returns balances for all addresses in the wallet
   */
  async getBalance(): Promise<Record<string, BalanceResponse[]>> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    // getBalance() is called without parameters - returns balances for all addresses
    return this.provider.getBalance();
  }

  /**
   * Get networks
   */
  async getNetworks(): Promise<NetworkInfo> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.getNetworks();
  }

  /**
   * Invoke contract method (read-only)
   */
  async invokeRead(
    scriptHash: string,
    operation: string,
    args: Array<{ type: string; value: any }>,
    signers?: Array<{ account: string; scopes: string }>
  ): Promise<InvokeResult> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.invokeRead({
      scriptHash,
      operation,
      args,
      signers: signers || [],
    });
  }

  /**
   * Invoke contract method (write - requires signing)
   */
  async invoke(
    scriptHash: string,
    operation: string,
    args: Array<{ type: string; value: any }>,
    options?: {
      fee?: string;
      extraSystemFee?: string;
      overrideSystemFee?: string;
      broadcastOverride?: boolean;
      signers?: Array<{
        account: string;
        scopes: number;
        allowedContracts?: string[];
        allowedGroups?: string[];
      }>;
    }
  ): Promise<InvokeResult> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.invoke({
      scriptHash,
      operation,
      args,
      fee: options?.fee,
      extraSystemFee: options?.extraSystemFee,
      overrideSystemFee: options?.overrideSystemFee,
      broadcastOverride: options?.broadcastOverride || false,
      signers: options?.signers || [],
    });
  }

  /**
   * Sign message
   */
  async signMessage(message: string): Promise<string> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.signMessage({
      message,
    });
  }

  /**
   * Add event listener
   */
  addEventListener(event: string, callback: (data: any) => void): void {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    this.provider.addEventListener(event, callback);
  }

  /**
   * Remove event listener
   */
  removeEventListener(event: string, callback: (data: any) => void): void {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    this.provider.removeEventListener(event, callback);
  }
}

// Singleton instance
let neolineInstance: NeoLineN3 | null = null;

/**
 * Get or initialize NeoLine instance
 */
export async function getNeoLine(): Promise<NeoLineN3> {
  if (!neolineInstance) {
    neolineInstance = new NeoLineN3();
    await neolineInstance.init();
  }
  return neolineInstance;
}

/**
 * Check if NeoLine is available
 */
export function isNeoLineAvailable(): boolean {
  return typeof window !== "undefined" && !!window.NEOLineN3;
}

/**
 * Wait for NeoLine to be ready
 */
export function waitForNeoLine(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined") {
      reject(new Error("Not in browser environment"));
      return;
    }

    if (window.NEOLineN3) {
      resolve();
      return;
    }

    const readyHandler = () => {
      window.removeEventListener("NEOLine.N3.EVENT.READY", readyHandler);
      resolve();
    };

    window.addEventListener("NEOLine.N3.EVENT.READY", readyHandler);

    setTimeout(() => {
      window.removeEventListener("NEOLine.N3.EVENT.READY", readyHandler);
      reject(new Error("NeoLine N3 dAPI timeout"));
    }, 10000);
  });
}

// Contract addresses
export const GAS_CONTRACT_HASH = "0xd2a4cff31913016155e38e474a2c06d08be276cf";
export const NORO_CONTRACT_HASH = "0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a";

// Witness scope constants (from Neo N3)
export const WITNESS_SCOPE = {
  None: 0,
  CalledByEntry: 1,
  CustomContracts: 16,
  CustomGroups: 32,
  Global: 128,
};

/**
 * Buy YES shares in a prediction market
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @param amount Amount in smallest GAS unit (e.g., 100000000 for 1 GAS)
 */
export async function buyYes(
  marketId: string,
  amount: string
): Promise<InvokeResult> {
  const neoline = await getNeoLine();
  const account = await neoline.getAccount();

  const contractHash = NORO_CONTRACT_HASH;
  const client = new rpc.RPCClient("https://testnet1.neo.coz.io:443");

  console.log("Calling buyYes with:", {
    contractHash,
    marketId,
    amount,
    accountAddress: account.address,
  });

  // Convert Base58 address to script hash (hex string) for write functions
  // NeoLine getAccount() returns Base58 address (e.g., "NZUugGMmmmdY")
  // But signers need script hash (hex string, e.g., "2cab903ff032ac693f8514581665be534beac39f")
  let accountForSigner: string;

  if (account.address.startsWith("N")) {
    // Base58 address - convert to script hash (hex string without 0x)
    try {
      accountForSigner = wallet.getScriptHashFromAddress(account.address);
      // Remove 0x prefix if present (NeoLine expects hex string without 0x)
      accountForSigner = accountForSigner.replace(/^0x/, "");
      console.log("Converted Base58 to script hash:", accountForSigner);
    } catch (error) {
      console.error("Failed to convert address to script hash:", error);
      throw new Error("Failed to convert address to script hash");
    }
  } else {
    // Already a script hash (hex string)
    accountForSigner = account.address.replace(/^0x/, ""); // Remove 0x if present
  }

  try {
    const invokeParams = {
      scriptHash: contractHash,
      operation: "buyYes",
      args: [
        { type: "Integer", value: marketId },
        { type: "Integer", value: amount },
      ],
      fee: "0.0001",
      broadcastOverride: false,
      signers: [
        {
          account: accountForSigner,
          scopes: WITNESS_SCOPE.Global, // 128 - Global scope
        },
      ],
    };

    console.log("RPC", neoline);

    console.log("Invoke params:", JSON.stringify(invokeParams, null, 2));

    const result = await neoline.invoke(
      contractHash,
      "buyYes",
      [
        { type: "Integer", value: marketId },
        { type: "Integer", value: amount },
      ],
      {
        fee: "0.0001",
        broadcastOverride: false,
        signers: [
          {
            account: accountForSigner,
            scopes: WITNESS_SCOPE.Global, // 128 - Global scope
          },
        ],
      }
    );
    console.log("buyYes success:", result);
    return result;
  } catch (error: any) {
    console.error("buyYes error:", error);
    console.error("Error details:", {
      type: error.type,
      description: error.description,
      data: error.data,
      fullError: error,
    });
    throw error;
  }
}

/**
 * Buy NO shares in a prediction market
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @param amount Amount in smallest GAS unit (e.g., 100000000 for 1 GAS)
 */
export async function buyNo(
  marketId: string,
  amount: string
): Promise<InvokeResult> {
  const neoline = await getNeoLine();
  const account = await neoline.getAccount();

  const contractHash = NORO_CONTRACT_HASH;

  console.log("Calling buyNo with:", { contractHash, marketId, amount });

  // Convert Base58 address to script hash (hex string) for write functions
  let accountForSigner: string;

  if (account.address.startsWith("N")) {
    // Base58 address - convert to script hash (hex string without 0x)
    try {
      accountForSigner = wallet.getScriptHashFromAddress(account.address);
      // Remove 0x prefix if present (NeoLine expects hex string without 0x)
      accountForSigner = accountForSigner.replace(/^0x/, "");
      console.log("Converted Base58 to script hash:", accountForSigner);
    } catch (error) {
      console.error("Failed to convert address to script hash:", error);
      throw new Error("Failed to convert address to script hash");
    }
  } else {
    // Already a script hash (hex string)
    accountForSigner = account.address.replace(/^0x/, ""); // Remove 0x if present
  }

  // Try with CalledByEntry first (most compatible)
  // NeoLine should show popup for this
  try {
    const result = await neoline.invoke(
      contractHash,
      "buyNo",
      [
        { type: "Integer", value: marketId },
        { type: "Integer", value: amount },
      ],
      {
        fee: "0.01",
        signers: [
          {
            account: accountForSigner, // Use script hash, not Base58
            scopes: WITNESS_SCOPE.Global, // 128 - Global scope
          },
        ],
      }
    );
    console.log("buyNo success:", result);
    return result;
  } catch (error: any) {
    console.error("buyNo error:", error);
    // Re-throw to let caller handle it
    throw error;
  }
}

/**
 * Create a new prediction market
 * @param question Market question
 * @param description Market description
 * @param category Market category
 * @param resolveDate Unix timestamp in milliseconds (BigInteger)
 * @param oracleUrl Oracle URL for resolution
 */
export async function createMarket(
  question: string,
  description: string,
  category: string,
  resolveDate: string, // Unix timestamp in milliseconds as string
  oracleUrl: string
): Promise<InvokeResult> {
  console.log("createMarket: Starting...");
  console.log("createMarket: Parameters:", {
    question,
    description,
    category,
    resolveDate,
    oracleUrl,
  });

  try {
    // Check if NeoLine is available first
    if (!isNeoLineAvailable()) {
      throw new Error(
        "NeoLine wallet extension is not installed or not available. Please install NeoLine wallet extension."
      );
    }
    console.log("✅ NeoLine is available");

    console.log("createMarket: Getting NeoLine instance...");
    const neoline = await getNeoLine();
    console.log("createMarket: NeoLine instance obtained");

    // Verify provider is initialized
    if (!neoline || !(neoline as any).provider) {
      throw new Error(
        "NeoLine provider is not initialized. Please refresh the page and try again."
      );
    }
    console.log("✅ NeoLine provider is initialized");

    console.log(
      "createMarket: Getting account (this should trigger wallet popup if not connected)..."
    );
    const account = await neoline.getAccount();
    console.log("createMarket: Account obtained:", account);

    if (!account || !account.address) {
      throw new Error(
        "Failed to get account from NeoLine. Please make sure your wallet is connected."
      );
    }
    console.log("✅ Account retrieved successfully:", account.address);

    const contractHash = NORO_CONTRACT_HASH;

    console.log("Calling createMarket with:", {
      contractHash,
      question,
      description,
      category,
      resolveDate,
      oracleUrl,
    });

    // Convert Base58 address to script hash (hex string) for write functions
    let accountForSigner: string;

    if (account.address.startsWith("N")) {
      // Base58 address - convert to script hash (hex string without 0x)
      try {
        accountForSigner = wallet.getScriptHashFromAddress(account.address);
        // Remove 0x prefix if present (NeoLine expects hex string without 0x)
        accountForSigner = accountForSigner.replace(/^0x/, "");
        console.log("Converted Base58 to script hash:", accountForSigner);
      } catch (error) {
        console.error("Failed to convert address to script hash:", error);
        throw new Error("Failed to convert address to script hash");
      }
    } else {
      // Already a script hash (hex string)
      accountForSigner = account.address.replace(/^0x/, ""); // Remove 0x if present
    }

    console.log(
      "createMarket: Invoking contract (this should trigger transaction confirmation popup)..."
    );
    const result = await neoline.invoke(
      contractHash,
      "createMarket",
      [
        { type: "String", value: question },
        { type: "String", value: description },
        { type: "String", value: category },
        { type: "Integer", value: resolveDate },
        { type: "String", value: oracleUrl },
      ],
      {
        fee: "0.01",
        signers: [
          {
            account: accountForSigner, // Use script hash, not Base58
            scopes: WITNESS_SCOPE.Global, // 128 - Global scope
          },
        ],
      }
    );
    console.log("createMarket success:", result);
    return result;
  } catch (error: any) {
    console.error("createMarket error:", error);
    console.error("createMarket error details:", {
      message: error?.message,
      code: error?.code,
      type: error?.type,
      stack: error?.stack,
    });
    throw error;
  }
}

/**
 * Get market data (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 */
export async function getMarket(marketId: string): Promise<any> {
  const neoline = await getNeoLine();

  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getMarket", [
      { type: "Integer", value: marketId },
    ]);

    // Parse the result - MarketData struct from contract
    if (result.stack && result.stack.length > 0) {
      const marketData = result.stack[0].value;

      // Helper to extract value from {type, value} structure
      const extractValue = (item: any): any => {
        if (item === null || item === undefined) return null;
        if (typeof item === "object" && "value" in item) {
          return item.value;
        }
        return item;
      };

      // NeoLine might return struct as object or array
      // Handle both cases
      if (Array.isArray(marketData)) {
        // If it's an array, extract values from each item if needed
        return marketData.map(extractValue);
      } else if (typeof marketData === "object" && marketData !== null) {
        // If it's an object, convert to array format for consistency
        // MarketData struct order: Question, Description, Category, ResolveDate, OracleUrl, Creator, CreatedAt, Resolved, Outcome, YesShares, NoShares
        const extract = (
          key: string,
          altKey: string,
          index: number,
          defaultValue: any = ""
        ) => {
          const val =
            marketData[key] || marketData[altKey] || marketData[index];
          return extractValue(val) ?? defaultValue;
        };

        return [
          extract("Question", "question", 0, ""),
          extract("Description", "description", 1, ""),
          extract("Category", "category", 2, ""),
          extract("ResolveDate", "resolveDate", 3, "0"),
          extract("OracleUrl", "oracleUrl", 4, ""),
          extract("Creator", "creator", 5, ""),
          extract("CreatedAt", "createdAt", 6, "0"),
          extract("Resolved", "resolved", 7, false),
          extract("Outcome", "outcome", 8, false),
          extract("YesShares", "yesShares", 9, "0"),
          extract("NoShares", "noShares", 10, "0"),
        ];
      }
      return marketData;
    }
    return null;
  } catch (error: any) {
    console.error("getMarket error:", error);
    throw error;
  }
}

/**
 * Get total market count (read-only)
 */
export async function getMarketCount(): Promise<number> {
  const neoline = await getNeoLine();

  const contractHash = NORO_CONTRACT_HASH;

  try {
    console.log("🔍 [FRONTEND] Getting market count from contract...");
    const result = await neoline.invokeRead(contractHash, "getMarketCount", []);
    console.log("📊 [FRONTEND] Market count result:", result);

    if (result.stack && result.stack.length > 0) {
      const count = result.stack[0].value;
      const parsedCount = parseInt(count, 10);
      console.log(`✅ [FRONTEND] Market count: ${parsedCount}`);
      return parsedCount;
    }
    console.log("⚠️ [FRONTEND] No stack in market count result");
    return 0;
  } catch (error: any) {
    console.error("❌ [FRONTEND] getMarketCount error:", error);
    return 0;
  }
}

/**
 * Fetch all markets directly from contract (read-only)
 * This bypasses the backend and reads directly from the blockchain
 */
export async function fetchAllMarketsFromContract(): Promise<Market[]> {
  try {
    console.log("🔍 [FRONTEND] Fetching all markets from contract...");

    // Get market count first
    const marketCount = await getMarketCount();
    console.log(`📊 [FRONTEND] Found ${marketCount} markets in contract`);

    if (marketCount === 0) {
      console.log("⚠️ [FRONTEND] No markets found in contract");
      return [];
    }

    const neoline = await getNeoLine();
    const contractHash = NORO_CONTRACT_HASH;
    const markets: Market[] = [];

    // Fetch each market (markets are 1-indexed)
    for (let i = 1; i <= marketCount; i++) {
      try {
        console.log(`🔍 [FRONTEND] Fetching market ${i}/${marketCount}...`);
        const marketData = await getMarket(String(i));

        if (
          marketData &&
          Array.isArray(marketData) &&
          marketData.length >= 11
        ) {
          // Helper function to extract value from {type, value} structure
          const extractValue = (item: any): any => {
            if (item === null || item === undefined) return "";
            if (typeof item === "object" && "value" in item) {
              return item.value;
            }
            return item;
          };

          // Parse market data array
          // MarketData struct: [Question, Description, Category, ResolveDate, OracleUrl, Creator, CreatedAt, Resolved, Outcome, YesShares, NoShares]
          // Each item might be wrapped in {type, value} structure
          const question = String(extractValue(marketData[0]) || "");
          const description = String(extractValue(marketData[1]) || "");
          const category = String(extractValue(marketData[2]) || "Others");
          const resolveDate = String(extractValue(marketData[3]) || "0");
          const oracleUrl = String(extractValue(marketData[4]) || "");
          const creator = String(extractValue(marketData[5]) || "");
          const createdAt = String(extractValue(marketData[6]) || "0");
          const resolved = Boolean(extractValue(marketData[7]) || false);
          const outcome = extractValue(marketData[8]);
          const yesShares = parseInt(
            String(extractValue(marketData[9]) || "0"),
            10
          );
          const noShares = parseInt(
            String(extractValue(marketData[10]) || "0"),
            10
          );

          // Calculate probability (yesShares / (yesShares + noShares) * 100)
          const totalShares = yesShares + noShares;
          const probability =
            totalShares > 0 ? Math.round((yesShares / totalShares) * 100) : 50;

          // Format volume
          const volume = formatVolume(yesShares, noShares);

          const market: Market = {
            id: String(i),
            question: question,
            description: description,
            category: category,
            resolveDate: resolveDate,
            probability: probability,
            volume: volume,
            isResolved: Boolean(resolved),
            outcome:
              outcome === true ? "Yes" : outcome === false ? "No" : undefined,
            creator: creator,
            created_at: createdAt,
            oracle_url: oracleUrl,
            yes_shares: yesShares,
            no_shares: noShares,
          };

          markets.push(market);
          const questionPreview =
            question && typeof question === "string"
              ? question.substring(0, 50)
              : String(question || "").substring(0, 50);
          console.log(`✅ [FRONTEND] Market ${i}: ${questionPreview}...`);
        } else {
          console.log(`⚠️ [FRONTEND] Market ${i} returned invalid data`);
        }
      } catch (error: any) {
        console.error(`❌ [FRONTEND] Error fetching market ${i}:`, error);
        // Continue to next market
        continue;
      }
    }

    console.log(
      `✅ [FRONTEND] Successfully fetched ${markets.length} markets from contract`
    );
    return markets;
  } catch (error: any) {
    console.error("❌ [FRONTEND] Error fetching all markets:", error);
    throw error;
  }
}

// Helper function to format volume
function formatVolume(yesShares: number, noShares: number): string {
  const total = yesShares + noShares;
  if (total === 0) return "0";
  if (total < 1000) return total.toString();
  if (total < 1000000) return `${(total / 1000).toFixed(1)}K`;
  return `${(total / 1000000).toFixed(1)}M`;
}

// Market interface for frontend
export interface Market {
  id: string;
  question: string;
  description?: string;
  category: string;
  resolveDate: string;
  probability: number;
  volume: string;
  isResolved: boolean;
  outcome?: "Yes" | "No";
  creator?: string;
  created_at?: string;
  oracle_url?: string;
  yes_shares?: number;
  no_shares?: number;
}

/**
 * Get market probability (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @returns Probability as number (0-10000, where 10000 = 100%)
 */
export async function getProbability(marketId: string): Promise<number> {
  const neoline = await getNeoLine();

  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getProbability", [
      { type: "Integer", value: marketId },
    ]);

    if (result.stack && result.stack.length > 0) {
      const probability = result.stack[0].value;
      return parseInt(probability, 10);
    }
    return 5000; // Default 50%
  } catch (error: any) {
    console.error("getProbability error:", error);
    return 5000;
  }
}

/**
 * Get user's YES shares for a market (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @param userAddress User address (UInt160 as string)
 */
export async function getUserYesShares(
  marketId: string,
  userAddress: string
): Promise<number> {
  const neoline = await getNeoLine();

  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getUserYesShares", [
      { type: "Integer", value: marketId },
      { type: "Hash160", value: userAddress },
    ]);

    if (result.stack && result.stack.length > 0) {
      const shares = result.stack[0].value;
      return parseInt(shares, 10);
    }
    return 0;
  } catch (error: any) {
    console.error("getUserYesShares error:", error);
    return 0;
  }
}

/**
 * Get user's NO shares for a market (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @param userAddress User address (UInt160 as string)
 */
export async function getUserNoShares(
  marketId: string,
  userAddress: string
): Promise<number> {
  const neoline = await getNeoLine();

  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getUserNoShares", [
      { type: "Integer", value: marketId },
      { type: "Hash160", value: userAddress },
    ]);

    if (result.stack && result.stack.length > 0) {
      const shares = result.stack[0].value;
      return parseInt(shares, 10);
    }
    return 0;
  } catch (error: any) {
    console.error("getUserNoShares error:", error);
    return 0;
  }
}

/**
 * ========== TEST FUNCTIONS ==========
 */

/**
 * Test simple connectivity
 */
export async function testSimple(): Promise<string> {
  const neoline = await getNeoLine();
  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "testSimple", []);
    if (result.stack && result.stack.length > 0) {
      return result.stack[0].value || "No response";
    }
    return "No response";
  } catch (error: any) {
    console.error("testSimple error:", error);
    throw error;
  }
}

/**
 * Test contract state
 */
export async function testContractState(): Promise<string> {
  const neoline = await getNeoLine();
  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(
      contractHash,
      "testContractState",
      []
    );
    if (result.stack && result.stack.length > 0) {
      return result.stack[0].value || "No response";
    }
    return "No response";
  } catch (error: any) {
    console.error("testContractState error:", error);
    throw error;
  }
}

/**
 * Test buyYes without executing
 */
export async function testBuyYes(
  marketId: string,
  amount: string
): Promise<string> {
  const neoline = await getNeoLine();
  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "testBuyYes", [
      { type: "Integer", value: marketId },
      { type: "Integer", value: amount },
    ]);
    if (result.stack && result.stack.length > 0) {
      return result.stack[0].value || "No response";
    }
    return "No response";
  } catch (error: any) {
    console.error("testBuyYes error:", error);
    throw error;
  }
}

/**
 * Test GAS transfer (write function - actually transfers GAS)
 * Uses the exact pattern from NeoLine docs example
 */
export async function testGasTransfer(amount: string): Promise<InvokeResult> {
  const neoline = await getNeoLine();
  const account = await neoline.getAccount();
  const contractHash = NORO_CONTRACT_HASH;

  console.log("Calling testGasTransfer with:", {
    contractHash,
    amount,
    accountAddress: account.address,
    accountScriptHash: account.scriptHash,
    accountType: account.address.startsWith("N")
      ? "Base58"
      : account.address.startsWith("0x")
      ? "ScriptHash"
      : "Unknown",
  });

  // In the example, account in signers is script hash (40 hex chars, no 0x)
  // Example: "2cab903ff032ac693f8514581665be534beac39f"
  // NeoLine getAccount() returns Base58 address, so we need to convert it
  let accountForSigner: string;

  // Try to get script hash - check multiple sources
  if (account.scriptHash) {
    accountForSigner = account.scriptHash.replace(/^0x/, "");
    console.log("Using scriptHash from account:", accountForSigner);
  } else if (neoline.provider && neoline.provider.addressToScriptHash) {
    // Try NeoLine's addressToScriptHash method
    try {
      const result = await neoline.provider.addressToScriptHash({
        address: account.address,
      });
      accountForSigner =
        result.scriptHash?.replace(/^0x/, "") || account.address;
      console.log("Got scriptHash from addressToScriptHash:", accountForSigner);
    } catch (e) {
      console.warn("addressToScriptHash failed, using address:", e);
      accountForSigner = account.address;
    }
  } else {
    // Last resort: try without account (let NeoLine auto-detect)
    // Or use address and hope NeoLine converts it
    accountForSigner = account.address;
    console.warn(
      "No script hash available. Using Base58 address - NeoLine might convert it."
    );
  }

  console.log(
    "Account for signer:",
    accountForSigner,
    "Length:",
    accountForSigner.length,
    "Format:",
    accountForSigner.length === 40 ? "ScriptHash" : "Base58"
  );

  try {
    const invokeParams = {
      scriptHash: contractHash,
      operation: "testGasTransfer",
      args: [{ type: "Integer", value: amount }],
      fee: "0.0001",
      broadcastOverride: false,
      signers: [
        {
          account: accountForSigner,
          scopes: WITNESS_SCOPE.CustomContracts, // 16
          allowedContracts: [contractHash, GAS_CONTRACT_HASH],
          allowedGroups: [],
        },
      ],
    };

    // Use provider.invoke directly to match the example pattern exactly
    // The example shows calling provider.invoke() with the full params object
    // If account is Base58, try without specifying it (let NeoLine auto-detect)
    let finalInvokeParams: any;

    if (accountForSigner.length === 40 && !accountForSigner.startsWith("N")) {
      // We have script hash - use it like in the example
      finalInvokeParams = invokeParams;
    } else {
      // We have Base58 - try without account (let NeoLine auto-detect)
      console.log(
        "Base58 address detected - trying without explicit account in signers"
      );
      finalInvokeParams = {
        scriptHash: contractHash,
        operation: "testGasTransfer",
        args: [{ type: "Integer", value: amount }],
        fee: "0.0001",
        broadcastOverride: false,
        signers: [], // Let NeoLine auto-detect
      };
    }

    console.log(
      "Final invoke params:",
      JSON.stringify(finalInvokeParams, null, 2)
    );

    // Call provider.invoke directly (matching the example)
    // Access provider through the class (it's private, so we use a workaround)
    const provider = (neoline as any)._provider;
    if (!provider) {
      throw new Error("NeoLine provider not available");
    }
    const result = await provider.invoke(finalInvokeParams);
    console.log("testGasTransfer success:", result);
    return result;
  } catch (error: any) {
    console.error("testGasTransfer error:", error);
    console.error("Error details:", {
      type: error.type,
      description: error.description,
      data: error.data,
      fullError: error,
    });

    // Try with CalledByEntry as fallback
    if (error.type === "RPC_ERROR") {
      console.log("Retrying testGasTransfer with CalledByEntry scope...");
      try {
        const result = await neoline.invoke(
          contractHash,
          "testGasTransfer",
          [{ type: "Integer", value: amount }],
          {
            fee: "0.0001",
            broadcastOverride: false,
            signers: [
              {
                account: accountForSigner,
                scopes: WITNESS_SCOPE.CalledByEntry,
              },
            ],
          }
        );
        console.log("testGasTransfer success (CalledByEntry):", result);
        return result;
      } catch (retryError: any) {
        console.error("testGasTransfer retry error:", retryError);
        // Try one more time without specifying account (let NeoLine auto-detect)
        console.log(
          "Retrying testGasTransfer without explicit signers (auto-detect)..."
        );
        try {
          const result = await neoline.invoke(
            contractHash,
            "testGasTransfer",
            [{ type: "Integer", value: amount }],
            {
              fee: "0.0001",
              broadcastOverride: false,
              signers: [], // Let NeoLine auto-detect the signer
            }
          );
          console.log("testGasTransfer success (auto-detect):", result);
          return result;
        } catch (finalError: any) {
          console.error("testGasTransfer final error:", finalError);
          throw finalError;
        }
      }
    }

    throw error;
  }
}

/**
 * Test storage operations
 */
export async function testStorage(marketId: string): Promise<string> {
  const neoline = await getNeoLine();
  const contractHash = NORO_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "testStorage", [
      { type: "Integer", value: marketId },
    ]);
    if (result.stack && result.stack.length > 0) {
      return result.stack[0].value || "No response";
    }
    return "No response";
  } catch (error: any) {
    console.error("testStorage error:", error);
    throw error;
  }
}

/**
 * Test function using the EXACT same code from NeoLine docs example
 * Uses the exact same contract, operation, and args from the example
 */
export async function testInvokeExample(): Promise<InvokeResult> {
  const neoline = await getNeoLine();
  const neolineN3 = neoline._provider;

  if (!neolineN3) {
    throw new Error("NeoLine provider not available");
  }

  // Use the EXACT same code from the example - no changes at all
  return neolineN3
    .invoke({
      scriptHash: "0x1415ab3b409a95555b77bc4ab6a7d9d7be0eddbd",
      operation: "transfer",
      args: [
        {
          type: "Address",
          value: "NaUjKgf5vMuFt7Ffgfffcpc41uH3adx1jq",
        },
        {
          type: "Address",
          value: "NaUjKgf5vMuFt7Ffgfffcpc41uH3adx1jq",
        },
        {
          type: "Integer",
          value: "1",
        },
        {
          type: "Any",
          value: null,
        },
      ],
      fee: "0.0001",
      broadcastOverride: false,
      signers: [
        {
          account: "2cab903ff032ac693f8514581665be534beac39f",
          scopes: 16,
          allowedContracts: [
            "0x1415ab3b409a95555b77bc4ab6a7d9d7be0eddbd",
            "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5",
          ],
          allowedGroups: [],
        },
      ],
    })
    .then((result) => {
      console.log("Invoke transaction success!");
      console.log("Transaction ID: " + result.txid);
      console.log("RPC node URL: " + result.nodeURL);
      return result;
    })
    .catch((error) => {
      const { type, description, data } = error;
      switch (type) {
        case "NO_PROVIDER":
          console.log("No provider available.");
          break;
        case "RPC_ERROR":
          console.log(
            "There was an error when broadcasting this transaction to the network."
          );
          break;
        case "CANCELED":
          console.log("The user has canceled this transaction.");
          break;
        default:
          // Not an expected error object.  Just write the error to the console.
          console.error(error);
          break;
      }
      throw error;
    });
}

export { NeoLineN3 };
export type {
  AccountInfo,
  BalanceResponse,
  NetworkInfo,
  TransactionData,
  InvokeResult,
};
