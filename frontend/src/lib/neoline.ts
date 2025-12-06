/**
 * NeoLine N3 dAPI Integration
 * Based on: https://neoline.io/dapi/N3.html
 *
 * This module provides API-based integration with NeoLine wallet
 * No SDK - using direct API calls as per requirements
 */

// import { rpc } from "viem/utils";
import { RpcClient } from "neo-mamba";

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
          // const client = new RpcClient("https://testnet1.neo.coz.io:443")
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
export const PREDICTX_CONTRACT_HASH =
  "0x76834b08fe30a94c0d7c722454b9a2e7b1d61e3a";

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

  const contractHash = PREDICTX_CONTRACT_HASH;

  console.log("Calling buyYes with:", {
    contractHash,
    marketId,
    amount,
    accountAddress: account.address,
  });

  // Match the example pattern exactly:
  // - Use CustomContracts scope (16)
  // - Include both PredictX and GAS contracts in allowedContracts
  // - Include allowedGroups: []
  // - Use lower fee (0.0001)
  // - Use broadcastOverride: false
  // Note: In the example, account is script hash (hex without 0x)
  // NeoLine getAccount() returns Base58 address, but signers might accept both
  const accountForSigner = account.address.replace(/^0x/, ""); // Remove 0x if present

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
          scopes: WITNESS_SCOPE.CustomContracts, // 16
          allowedContracts: [
            accountForSigner, // GAS contract (with 0x)
          ],
          allowedGroups: [],
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
            scopes: WITNESS_SCOPE.CustomContracts,
            allowedContracts: [contractHash, GAS_CONTRACT_HASH],
            allowedGroups: [],
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

  // Keep 0x prefix - NeoLine might need it
  const contractHash = PREDICTX_CONTRACT_HASH;

  console.log("Calling buyNo with:", { contractHash, marketId, amount });

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
            account: account.address,
            scopes: WITNESS_SCOPE.CalledByEntry,
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
  const neoline = await getNeoLine();
  const account = await neoline.getAccount();

  const contractHash = PREDICTX_CONTRACT_HASH;

  console.log("Calling createMarket with:", {
    contractHash,
    question,
    description,
    category,
    resolveDate,
    oracleUrl,
  });

  try {
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
            account: account.address,
            scopes: WITNESS_SCOPE.CalledByEntry,
          },
        ],
      }
    );
    console.log("createMarket success:", result);
    return result;
  } catch (error: any) {
    console.error("createMarket error:", error);
    throw error;
  }
}

/**
 * Get market data (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 */
export async function getMarket(marketId: string): Promise<any> {
  const neoline = await getNeoLine();

  const contractHash = PREDICTX_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getMarket", [
      { type: "Integer", value: marketId },
    ]);

    // Parse the result - MarketData struct from contract
    if (result.stack && result.stack.length > 0) {
      const marketData = result.stack[0].value;

      // NeoLine might return struct as object or array
      // Handle both cases
      if (Array.isArray(marketData)) {
        // If it's an array, return as-is
        return marketData;
      } else if (typeof marketData === "object" && marketData !== null) {
        // If it's an object, convert to array format for consistency
        // MarketData struct order: Id, Question, Description, Category, ResolveDate, OracleUrl, Creator, CreatedAt, Resolved, Outcome, YesShares, NoShares
        return [
          marketData.Question || marketData.question || marketData[0] || "",
          marketData.Description ||
            marketData.description ||
            marketData[1] ||
            "",
          marketData.Category || marketData.category || marketData[2] || "",
          marketData.ResolveDate ||
            marketData.resolveDate ||
            marketData[3] ||
            "0",
          marketData.OracleUrl || marketData.oracleUrl || marketData[4] || "",
          marketData.Creator || marketData.creator || marketData[5] || "",
          marketData.CreatedAt || marketData.createdAt || marketData[6] || "0",
          marketData.Resolved || marketData.resolved || marketData[7] || false,
          marketData.Outcome || marketData.outcome || marketData[8] || false,
          marketData.YesShares || marketData.yesShares || marketData[9] || "0",
          marketData.NoShares || marketData.noShares || marketData[10] || "0",
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

  const contractHash = PREDICTX_CONTRACT_HASH;

  try {
    const result = await neoline.invokeRead(contractHash, "getMarketCount", []);

    if (result.stack && result.stack.length > 0) {
      const count = result.stack[0].value;
      return parseInt(count, 10);
    }
    return 0;
  } catch (error: any) {
    console.error("getMarketCount error:", error);
    return 0;
  }
}

/**
 * Get market probability (read-only)
 * @param marketId Market ID (as BigInteger string, e.g., "1")
 * @returns Probability as number (0-10000, where 10000 = 100%)
 */
export async function getProbability(marketId: string): Promise<number> {
  const neoline = await getNeoLine();

  const contractHash = PREDICTX_CONTRACT_HASH;

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

  const contractHash = PREDICTX_CONTRACT_HASH;

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

  const contractHash = PREDICTX_CONTRACT_HASH;

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
  const contractHash = PREDICTX_CONTRACT_HASH;

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
  const contractHash = PREDICTX_CONTRACT_HASH;

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
  const contractHash = PREDICTX_CONTRACT_HASH;

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
  const contractHash = PREDICTX_CONTRACT_HASH;

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
  const contractHash = PREDICTX_CONTRACT_HASH;

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
