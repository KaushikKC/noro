/**
 * NeoLine N3 dAPI Integration
 * Based on: https://neoline.io/dapi/N3.html
 *
 * This module provides API-based integration with NeoLine wallet
 * No SDK - using direct API calls as per requirements
 */

// Type definitions based on NeoLine dAPI documentation
interface NeoLineProvider {
  name: string;
  website: string;
  version: string;
  compatibility: string[];
  extra: Record<string, any>;
}

interface AccountInfo {
  address: string;
  label?: string;
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
  signers?: Array<{
    account: string;
    scopes: string;
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
    return this.provider.getAccount();
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
    signers?: Array<{ account: string; scopes: string }>
  ): Promise<InvokeResult> {
    if (!this.provider) {
      throw new Error("NeoLine not initialized. Call init() first.");
    }
    return this.provider.invoke({
      scriptHash,
      operation,
      args,
      signers: signers || [],
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

export { NeoLineN3 };
export type {
  AccountInfo,
  BalanceResponse,
  NetworkInfo,
  TransactionData,
  InvokeResult,
};
