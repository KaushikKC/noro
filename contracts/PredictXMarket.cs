using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Attributes;
using Neo.SmartContract.Framework.Native;
using Neo.SmartContract.Framework.Services;
using System;
using System.ComponentModel;
using System.Numerics;

namespace noro
{
    [DisplayName("NoroMarket")]
    [ContractAuthor("noro-team", "dev@noro.io")]
    [ContractVersion("0.1.0")]
    [ContractPermission("*")]
    [ContractDescription("Decentralized AI-powered prediction market platform on Neo blockchain")]
    public class NoroMarket : SmartContract
    {
        // Contract owner - TODO: Replace with actual owner address (use your wallet's script hash)
        // Format: 0x followed by 40 hex characters (20 bytes)
        [InitialValue("0x0000000000000000000000000000000000000000", ContractParameterType.Hash160)]
        static readonly UInt160 Owner = default!;

        // Helper method to convert string to byte array
        private static byte[] StringToBytes(string str)
        {
            byte[] result = new byte[str.Length];
            for (int i = 0; i < str.Length; i++)
            {
                result[i] = (byte)str[i];
            }
            return result;
        }

        // Safe transfer helper using Contract.Call (more reliable than direct GAS.Transfer)
        private static bool SafeTransfer(UInt160 token, UInt160 from, UInt160 to, BigInteger amount, object data)
        {
            try
            {
                var result = (bool)Contract.Call(token, "transfer", CallFlags.All, new object[] { from, to, amount, data });
                return result;
            }
            catch (Exception)
            {
                return false;
            }
        }

        // Storage prefixes
        private static readonly byte[] MarketCountKey = StringToBytes("marketCount");
        private static readonly byte[] MarketPrefix = StringToBytes("market");
        private static readonly byte[] QuestionPrefix = StringToBytes("question");
        private static readonly byte[] DescPrefix = StringToBytes("desc");
        private static readonly byte[] CategoryPrefix = StringToBytes("cat");
        private static readonly byte[] ResolveDatePrefix = StringToBytes("resolveDate");
        private static readonly byte[] OracleUrlPrefix = StringToBytes("oracleUrl");
        private static readonly byte[] CreatorPrefix = StringToBytes("creator");
        private static readonly byte[] CreatedAtPrefix = StringToBytes("createdAt");
        private static readonly byte[] YesSharesPrefix = StringToBytes("yesShares");
        private static readonly byte[] NoSharesPrefix = StringToBytes("noShares");
        private static readonly byte[] ResolvedPrefix = StringToBytes("resolved");
        private static readonly byte[] OutcomePrefix = StringToBytes("outcome");

        // Events
        [DisplayName("MarketCreated")]
        public static event Action<string, string, string, BigInteger, string> OnMarketCreated = default!;

        [DisplayName("TradeExecuted")]
        public static event Action<string, UInt160, bool, BigInteger> OnTradeExecuted = default!;

        [DisplayName("MarketResolved")]
        public static event Action<string, bool> OnMarketResolved = default!;

        [DisplayName("PayoutDistributed")]
        public static event Action<string, UInt160, BigInteger> OnPayoutDistributed = default!;

        // Verification trigger - checks if caller is owner
        public static bool Verify() => Runtime.CheckWitness(Owner);

        // Check if caller is owner
        private static bool IsOwner() => Runtime.CheckWitness(Owner);

        // Create a new prediction market
        [DisplayName("createMarket")]
        public static string CreateMarket(
            string question,
            string description,
            string category,
            BigInteger resolveDate,
            string oracleUrl
        )
        {
            // Validate inputs
            if (question.Length == 0 || description.Length == 0)
                throw new Exception("Question and description cannot be empty");

            if (resolveDate <= Runtime.Time)
                throw new Exception("Resolve date must be in the future");

            // Generate market ID (increment counter)
            BigInteger marketCount = (BigInteger)Storage.Get(Storage.CurrentContext, MarketCountKey);
            marketCount += 1;
            Storage.Put(Storage.CurrentContext, MarketCountKey, marketCount);
            BigInteger marketId = marketCount;  // Use BigInteger as key

            // Store market data fields individually
            StorageMap questionMap = new(Storage.CurrentContext, QuestionPrefix);
            StorageMap descMap = new(Storage.CurrentContext, DescPrefix);
            StorageMap catMap = new(Storage.CurrentContext, CategoryPrefix);
            StorageMap resolveDateMap = new(Storage.CurrentContext, ResolveDatePrefix);
            StorageMap oracleUrlMap = new(Storage.CurrentContext, OracleUrlPrefix);
            StorageMap creatorMap = new(Storage.CurrentContext, CreatorPrefix);
            StorageMap createdAtMap = new(Storage.CurrentContext, CreatedAtPrefix);
            StorageMap yesSharesMap = new(Storage.CurrentContext, YesSharesPrefix);
            StorageMap noSharesMap = new(Storage.CurrentContext, NoSharesPrefix);
            StorageMap resolvedMap = new(Storage.CurrentContext, ResolvedPrefix);
            StorageMap outcomeMap = new(Storage.CurrentContext, OutcomePrefix);

            questionMap.Put((ByteString)marketId, question);
            descMap.Put((ByteString)marketId, description);
            catMap.Put((ByteString)marketId, category);
            resolveDateMap.Put((ByteString)marketId, resolveDate);
            oracleUrlMap.Put((ByteString)marketId, oracleUrl);
            creatorMap.Put((ByteString)marketId, Runtime.Transaction.Sender);
            createdAtMap.Put((ByteString)marketId, Runtime.Time);
            yesSharesMap.Put((ByteString)marketId, 0);
            noSharesMap.Put((ByteString)marketId, 0);
            resolvedMap.Put((ByteString)marketId, false);
            outcomeMap.Put((ByteString)marketId, false);

            // Emit event (convert to string for display)
            string marketIdStr = marketId.ToString();
            OnMarketCreated(marketIdStr, question, category, resolveDate, oracleUrl);

            return marketIdStr;
        }

        // Buy YES shares
        // Note: User must send GAS to the contract FIRST, then call this method
        // The GAS will be received via OnNEP17Payment callback
        [DisplayName("buyYes")]
        public static bool BuyYes(BigInteger marketId, BigInteger amount)
        {
            if (amount <= 0)
                throw new Exception("Amount must be greater than 0");

            // Get market data
            MarketData market = GetMarket(marketId);
            if (market == null)
                throw new Exception("Market not found");

            if (market.Resolved)
                throw new Exception("Market is already resolved");

            if (Runtime.Time >= market.ResolveDate)
                throw new Exception("Market resolve date has passed");

            // Check for payment in current transaction or pending payments
            // OnNEP17Payment is called BEFORE buyYes in the same transaction
            UInt160 caller = Runtime.Transaction.Sender;
            
            // Check if payment was received in this transaction or previously
            StorageMap pendingPaymentsMap = new(Storage.CurrentContext, StringToBytes("pendingPay"));
            string paymentKey = caller.ToString() + "_" + marketId.ToString() + "_yes";
            
            // Also check for transaction-scoped payment (same transaction)
            // Use a shorter key - just use caller + marketId + side (transaction hash is too long)
            string txPaymentKey = "tx_" + caller.ToString() + "_" + marketId.ToString() + "_yes";
            var txPaymentAmount = pendingPaymentsMap.Get((ByteString)txPaymentKey);
            var paymentAmount = pendingPaymentsMap.Get((ByteString)paymentKey);
            
            BigInteger availableAmount = 0;
            if (txPaymentAmount != null)
                availableAmount = (BigInteger)txPaymentAmount;
            if (paymentAmount != null)
                availableAmount += (BigInteger)paymentAmount;
            
            if (availableAmount < amount)
            {
                // Try to use Contract.Call to transfer GAS from user (requires user as signer)
                // This works if the transaction includes the user as a signer
                object transferData = marketId.ToString() + "_yes";
                if (!SafeTransfer(GAS.Hash, caller, Runtime.ExecutingScriptHash, amount, transferData))
                {
                    throw new Exception($"Insufficient payment. Received: {availableAmount}, Required: {amount}. Please ensure GAS transfer is included in the transaction or send GAS to contract with data '{marketId}_yes'.");
                }
                // If transfer succeeded, OnNEP17Payment will be called, then we continue
                // Re-check payment after transfer
                txPaymentAmount = pendingPaymentsMap.Get((ByteString)txPaymentKey);
                paymentAmount = pendingPaymentsMap.Get((ByteString)paymentKey);
                availableAmount = 0;
                if (txPaymentAmount != null)
                    availableAmount = (BigInteger)txPaymentAmount;
                if (paymentAmount != null)
                    availableAmount += (BigInteger)paymentAmount;
                if (availableAmount < amount)
                    throw new Exception($"Payment verification failed after transfer. Please try again.");
            }
            
            // Clear the payments (consume them)
            if (txPaymentAmount != null)
                pendingPaymentsMap.Delete((ByteString)txPaymentKey);
            if (paymentAmount != null)
            {
                BigInteger remaining = (BigInteger)paymentAmount - amount;
                if (remaining > 0)
                    pendingPaymentsMap.Put((ByteString)paymentKey, remaining);
                else
                    pendingPaymentsMap.Delete((ByteString)paymentKey);
            }

            // Update shares
            StorageMap yesSharesMap = new(Storage.CurrentContext, YesSharesPrefix);
            var currentYesSharesValue = yesSharesMap.Get((ByteString)marketId);
            BigInteger currentYesShares = currentYesSharesValue is null ? 0 : (BigInteger)currentYesSharesValue;
            currentYesShares += amount;
            yesSharesMap.Put((ByteString)marketId, currentYesShares);

            // Track user shares (for payout calculation)
            StorageMap userYesSharesMap = new(Storage.CurrentContext, StringToBytes("userYes"));
            string userYesKey = marketId.ToString() + "_yes_" + caller.ToString();
            var userYesSharesValue = userYesSharesMap.Get((ByteString)userYesKey);
            BigInteger userYesShares = userYesSharesValue is null ? 0 : (BigInteger)userYesSharesValue;
            userYesShares += amount;
            userYesSharesMap.Put((ByteString)userYesKey, userYesShares);

            // Emit event
            OnTradeExecuted(marketId.ToString(), caller, true, amount);

            return true;
        }

        // Buy NO shares
        // Note: User must send GAS to the contract FIRST, then call this method
        // The GAS will be received via OnNEP17Payment callback
        [DisplayName("buyNo")]
        public static bool BuyNo(BigInteger marketId, BigInteger amount)
        {
            if (amount <= 0)
                throw new Exception("Amount must be greater than 0");

            // Get market data
            MarketData market = GetMarket(marketId);
            if (market == null)
                throw new Exception("Market not found");

            if (market.Resolved)
                throw new Exception("Market is already resolved");

            if (Runtime.Time >= market.ResolveDate)
                throw new Exception("Market resolve date has passed");

            // Check for payment in current transaction or pending payments
            // OnNEP17Payment is called BEFORE buyNo in the same transaction
            UInt160 caller = Runtime.Transaction.Sender;
            
            // Check if payment was received in this transaction or previously
            StorageMap pendingPaymentsMap = new(Storage.CurrentContext, StringToBytes("pendingPay"));
            string paymentKey = caller.ToString() + "_" + marketId.ToString() + "_no";
            
            // Also check for transaction-scoped payment (same transaction)
            // Use a shorter key - just use caller + marketId + side (transaction hash is too long)
            string txPaymentKey = "tx_" + caller.ToString() + "_" + marketId.ToString() + "_no";
            var txPaymentAmount = pendingPaymentsMap.Get((ByteString)txPaymentKey);
            var paymentAmount = pendingPaymentsMap.Get((ByteString)paymentKey);
            
            BigInteger availableAmount = 0;
            if (txPaymentAmount != null)
                availableAmount = (BigInteger)txPaymentAmount;
            if (paymentAmount != null)
                availableAmount += (BigInteger)paymentAmount;
            
            if (availableAmount < amount)
            {
                // Try to use Contract.Call to transfer GAS from user (requires user as signer)
                // This works if the transaction includes the user as a signer
                object transferData = marketId.ToString() + "_no";
                if (!SafeTransfer(GAS.Hash, caller, Runtime.ExecutingScriptHash, amount, transferData))
                {
                    throw new Exception($"Insufficient payment. Received: {availableAmount}, Required: {amount}. Please ensure GAS transfer is included in the transaction or send GAS to contract with data '{marketId}_no'.");
                }
                // If transfer succeeded, OnNEP17Payment will be called, then we continue
                // Re-check payment after transfer
                txPaymentAmount = pendingPaymentsMap.Get((ByteString)txPaymentKey);
                paymentAmount = pendingPaymentsMap.Get((ByteString)paymentKey);
                availableAmount = 0;
                if (txPaymentAmount != null)
                    availableAmount = (BigInteger)txPaymentAmount;
                if (paymentAmount != null)
                    availableAmount += (BigInteger)paymentAmount;
                if (availableAmount < amount)
                    throw new Exception($"Payment verification failed after transfer. Please try again.");
            }
            
            // Clear the payments (consume them)
            if (txPaymentAmount != null)
                pendingPaymentsMap.Delete((ByteString)txPaymentKey);
            if (paymentAmount != null)
            {
                BigInteger remaining = (BigInteger)paymentAmount - amount;
                if (remaining > 0)
                    pendingPaymentsMap.Put((ByteString)paymentKey, remaining);
                else
                    pendingPaymentsMap.Delete((ByteString)paymentKey);
            }

            // Update shares
            StorageMap noSharesMap = new(Storage.CurrentContext, NoSharesPrefix);
            var currentNoSharesValue = noSharesMap.Get((ByteString)marketId);
            BigInteger currentNoShares = currentNoSharesValue is null ? 0 : (BigInteger)currentNoSharesValue;
            currentNoShares += amount;
            noSharesMap.Put((ByteString)marketId, currentNoShares);

            // Track user shares (for payout calculation)
            StorageMap userNoSharesMap = new(Storage.CurrentContext, StringToBytes("userNo"));
            string userNoKey = marketId.ToString() + "_no_" + caller.ToString();
            var userNoSharesValue = userNoSharesMap.Get((ByteString)userNoKey);
            BigInteger userNoShares = userNoSharesValue is null ? 0 : (BigInteger)userNoSharesValue;
            userNoShares += amount;
            userNoSharesMap.Put((ByteString)userNoKey, userNoShares);

            // Emit event
            OnTradeExecuted(marketId.ToString(), caller, false, amount);

            return true;
        }

        // Request oracle resolution
        // According to Neo Oracle documentation:
        // Oracle.Request(url, filter, callback, userData, gasForResponse)
        // - url: max 256 bytes, must return JSON
        // - filter: JSONPath expression, max 128 bytes
        // - callback: method name (cannot begin with "_"), max 32 bytes
        // - userData: byte array (we pass marketId as bytes)
        // - gasForResponse: minimum 0.1 GAS (10000000)
        [DisplayName("requestResolve")]
        public static void RequestResolve(BigInteger marketId, string oracleUrl, string filter, long gasForResponse)
        {
            // Get market data
            MarketData market = GetMarket(marketId);
            if (market == null)
                throw new Exception("Market not found");

            if (market.Resolved)
                throw new Exception("Market is already resolved");

            if (Runtime.Time < market.ResolveDate)
                throw new Exception("Market resolve date has not arrived");

            // Convert marketId to byte array for userData
            // Oracle.Request signature: (string url, string filter, string callback, byte[] userData, long gasForResponse)
            byte[] marketIdBytes = StringToBytes(marketId.ToString());
            
            // Minimum gasForResponse is 0.1 GAS (10000000 in smallest unit)
            if (gasForResponse < 10000000)
                gasForResponse = 10000000;
            
            // Request oracle - callback method name is "onOracleCallback"
            Oracle.Request(oracleUrl, filter, "onOracleCallback", marketIdBytes, gasForResponse);
        }

        // Oracle callback handler
        // According to Neo Oracle documentation, callback signature must be:
        // Callback(string url, byte[] userData, int code, byte[] result)
        // - url: Original request URL
        // - userData: Custom data passed in request (marketId as bytes)
        // - code: Response code (0 = success, non-zero = error)
        // - result: Filtered result data as bytes (JSON string)
        [DisplayName("onOracleCallback")]
        public static void OnOracleCallback(string url, byte[] userData, int code, byte[] result)
        {
            // Only oracle can call this - verify calling script hash
            if (Runtime.CallingScriptHash != Oracle.Hash)
                throw new Exception("Unauthorized! Only Oracle can call this method");

            // Check if request was successful (code 0 = success)
            if (code != 0)
                throw new Exception($"Oracle request failed with code: {code}");

            // Convert userData (marketId bytes) back to string, then to BigInteger
            string marketIdString = "";
            for (int i = 0; i < userData.Length; i++)
            {
                marketIdString += (char)userData[i];
            }
            BigInteger marketId = BigInteger.Parse(marketIdString);

            MarketData market = GetMarket(marketId);
            if (market == null)
                throw new Exception("Market not found");

            if (market.Resolved)
                throw new Exception("Market is already resolved");

            // Convert result bytes to string for parsing
            // Oracle returns filtered JSON data based on the filter expression
            string resultString = "";
            for (int i = 0; i < result.Length; i++)
            {
                resultString += (char)result[i];
            }

            // Parse oracle result (expecting JSON with "outcome": "YES" or "NO")
            // The filter should extract the outcome field, e.g., "$.outcome"
            bool outcome = false;
            if (resultString.Contains("\"outcome\":\"YES\"") || 
                resultString.Contains("'outcome':'YES'") || 
                resultString.Contains("\"outcome\":\"yes\"") ||
                resultString.Contains("\"outcome\":\"Yes\"") ||
                resultString.ToUpper().Contains("YES") ||
                resultString.Trim() == "\"YES\"" ||
                resultString.Trim() == "YES")
            {
                outcome = true;
            }
            else if (resultString.Contains("\"outcome\":\"NO\"") || 
                     resultString.Contains("'outcome':'NO'") || 
                     resultString.Contains("\"outcome\":\"no\"") ||
                     resultString.Contains("\"outcome\":\"No\"") ||
                     resultString.ToUpper().Contains("NO") ||
                     resultString.Trim() == "\"NO\"" ||
                     resultString.Trim() == "NO")
            {
                outcome = false;
            }
            else
            {
                throw new Exception($"Invalid oracle result format. Expected JSON with 'outcome' field. Got: {resultString}");
            }

            // Store resolved state
            byte[] marketIdBytes = StringToBytes(marketId.ToString());
            StorageMap resolvedMap = new(Storage.CurrentContext, ResolvedPrefix);
            StorageMap outcomeMap = new(Storage.CurrentContext, OutcomePrefix);
            resolvedMap.Put(marketIdBytes, (byte)1);  // Store as byte 1 for true
            outcomeMap.Put(marketIdBytes, outcome ? (byte)1 : (byte)0);  // Store as byte

            // Emit event
            OnMarketResolved(marketId.ToString(), outcome);
        }

        // Distribute payouts to winners
        [DisplayName("payout")]
        public static bool Payout(BigInteger marketId)
        {
            MarketData market = GetMarket(marketId);
            if (market == null)
                throw new Exception("Market not found");

            if (!market.Resolved)
                throw new Exception("Market is not resolved yet");

            // Calculate total pool
            BigInteger totalPool = market.YesShares + market.NoShares;
            if (totalPool == 0)
                throw new Exception("No shares in market");

            // Determine winning side
            bool winningSide = market.Outcome; // true = YES, false = NO

            // Get contract balance
            BigInteger contractBalance = GAS.BalanceOf(Runtime.ExecutingScriptHash);

            // Distribute to YES winners if YES won
            if (winningSide && market.YesShares > 0)
            {
                // Calculate payout per share
                BigInteger payoutPerShare = contractBalance * market.YesShares / totalPool / market.YesShares;
                // Note: In production, you'd iterate through all YES holders and distribute
                // For now, this is a simplified version
            }

            // Distribute to NO winners if NO won
            if (!winningSide && market.NoShares > 0)
            {
                // Calculate payout per share
                BigInteger payoutPerShare = contractBalance * market.NoShares / totalPool / market.NoShares;
                // Note: In production, you'd iterate through all NO holders and distribute
            }

            // Emit event (simplified - in production, emit for each winner)
            OnPayoutDistributed(marketId.ToString(), Runtime.Transaction.Sender, contractBalance);

            return true;
        }

        // Get market data
        [Safe]
        [DisplayName("getMarket")]
        public static MarketData? GetMarket(BigInteger marketId)
        {
            
            StorageMap questionMap = new(Storage.CurrentContext, QuestionPrefix);
            string? question = (string?)questionMap.Get((ByteString)marketId);
            if (question == null)
                return null;

            StorageMap descMap = new(Storage.CurrentContext, DescPrefix);
            StorageMap catMap = new(Storage.CurrentContext, CategoryPrefix);
            StorageMap resolveDateMap = new(Storage.CurrentContext, ResolveDatePrefix);
            StorageMap oracleUrlMap = new(Storage.CurrentContext, OracleUrlPrefix);
            StorageMap creatorMap = new(Storage.CurrentContext, CreatorPrefix);
            StorageMap createdAtMap = new(Storage.CurrentContext, CreatedAtPrefix);
            StorageMap yesSharesMap = new(Storage.CurrentContext, YesSharesPrefix);
            StorageMap noSharesMap = new(Storage.CurrentContext, NoSharesPrefix);
            StorageMap resolvedMap = new(Storage.CurrentContext, ResolvedPrefix);
            StorageMap outcomeMap = new(Storage.CurrentContext, OutcomePrefix);

            var yesSharesValue = yesSharesMap.Get((ByteString)marketId);
            var noSharesValue = noSharesMap.Get((ByteString)marketId);
            var resolvedValue = resolvedMap.Get((ByteString)marketId);
            var outcomeValue = outcomeMap.Get((ByteString)marketId);
            
            BigInteger yesShares = yesSharesValue is null ? 0 : (BigInteger)yesSharesValue;
            BigInteger noShares = noSharesValue is null ? 0 : (BigInteger)noSharesValue;
            
            // Properly convert ByteString to bool: check actual byte value, not just length
            bool resolved = false;
            bool outcome = false;
            if (resolvedValue != null)
            {
                ByteString resolvedBytes = (ByteString)resolvedValue;
                // A boolean stored as ByteString: empty or [0x00] = false, [0x01] or non-empty = true
                resolved = resolvedBytes.Length > 0 && resolvedBytes[0] != 0;
            }
            if (outcomeValue != null)
            {
                ByteString outcomeBytes = (ByteString)outcomeValue;
                outcome = outcomeBytes.Length > 0 && outcomeBytes[0] != 0;
            }

            return new MarketData
            {
                Id = marketId.ToString(),
                Question = question,
                Description = (string)descMap.Get((ByteString)marketId),
                Category = (string)catMap.Get((ByteString)marketId),
                ResolveDate = (BigInteger)resolveDateMap.Get((ByteString)marketId),
                OracleUrl = (string)oracleUrlMap.Get((ByteString)marketId),
                Creator = (UInt160)creatorMap.Get((ByteString)marketId),
                CreatedAt = (BigInteger)createdAtMap.Get((ByteString)marketId),
                Resolved = resolved,
                Outcome = outcome,
                YesShares = yesShares,
                NoShares = noShares
            };
        }

        // Get current probability (YES probability)
        [Safe]
        [DisplayName("getProbability")]
        public static BigInteger GetProbability(BigInteger marketId)
        {
            MarketData market = GetMarket(marketId);
            if (market == null)
                return 0;

            BigInteger totalShares = market.YesShares + market.NoShares;
            if (totalShares == 0)
                return 5000; // 50% default (represented as 5000/10000 for precision)

            // Calculate probability as percentage (0-10000, where 10000 = 100%)
            BigInteger probability = market.YesShares * 10000 / totalShares;
            return probability;
        }

        // Get total market count
        [Safe]
        [DisplayName("getMarketCount")]
        public static BigInteger GetMarketCount()
        {
            return (BigInteger)Storage.Get(Storage.CurrentContext, MarketCountKey);
        }

        // Get user's YES shares for a market
        [Safe]
        [DisplayName("getUserYesShares")]
        public static BigInteger GetUserYesShares(BigInteger marketId, UInt160 user)
        {
            StorageMap userYesSharesMap = new(Storage.CurrentContext, StringToBytes("userYes"));
            string userYesKey = marketId.ToString() + "_yes_" + user.ToString();
            var sharesValue = userYesSharesMap.Get((ByteString)userYesKey);
            return sharesValue is null ? 0 : (BigInteger)sharesValue;
        }

        // Get user's NO shares for a market
        [Safe]
        [DisplayName("getUserNoShares")]
        public static BigInteger GetUserNoShares(BigInteger marketId, UInt160 user)
        {
            StorageMap userNoSharesMap = new(Storage.CurrentContext, StringToBytes("userNo"));
            string userNoKey = marketId.ToString() + "_no_" + user.ToString();
            var sharesValue = userNoSharesMap.Get((ByteString)userNoKey);
            return sharesValue is null ? 0 : (BigInteger)sharesValue;
        }

        // Empty onPayment method (required by Neo team)
        // This allows the contract to receive NEP-17 tokens (GAS)
        [DisplayName("onPayment")]
        public static void OnPayment(UInt160 from, BigInteger amount, object data)
        {
            // Empty method as recommended by Neo team
            // This is required for the contract to receive NEP-17 token payments
        }

        // Handle NEP-17 token payments (GAS)
        // This is called automatically when someone sends GAS to this contract
        public static void OnNEP17Payment(UInt160 from, BigInteger amount, object data)
        {
            // Only accept GAS payments
            if (Runtime.CallingScriptHash != GAS.Hash)
                return;

            if (amount <= 0)
                return;

            // Parse data to extract marketId and side (yes/no)
            // Data format: "marketId_side" as string, e.g., "1_yes" or "1_no"
            if (data == null)
            {
                // No data provided - store as pending payment for manual processing
                // User will need to call buyYes/buyNo separately
                return;
            }

            // Parse data string: "marketId_side" (e.g., "1_yes")
            // Note: string.Split() is not available in Neo, so we parse manually
            string dataStr = (string)data;
            
            // Find the underscore separator
            int underscoreIndex = -1;
            for (int i = 0; i < dataStr.Length; i++)
            {
                if (dataStr[i] == '_')
                {
                    underscoreIndex = i;
                    break;
                }
            }
            
            if (underscoreIndex < 0 || underscoreIndex >= dataStr.Length - 1)
                throw new Exception("Invalid payment data format. Expected: 'marketId_side' (e.g., '1_yes')");

            // Extract marketId (before underscore)
            string marketIdStr = "";
            for (int i = 0; i < underscoreIndex; i++)
            {
                marketIdStr += dataStr[i];
            }
            
            // Extract side (after underscore)
            string side = "";
            for (int i = underscoreIndex + 1; i < dataStr.Length; i++)
            {
                char c = dataStr[i];
                // Convert to lowercase manually
                if (c >= 'A' && c <= 'Z')
                    c = (char)(c + 32);  // Convert to lowercase
                side += c;
            }
            
            BigInteger marketId = BigInteger.Parse(marketIdStr);

            if (side != "yes" && side != "no")
                throw new Exception("Invalid side. Must be 'yes' or 'no'");

            // Store pending payment (both transaction-scoped and user-scoped)
            StorageMap pendingPaymentsMap = new(Storage.CurrentContext, StringToBytes("pendingPay"));
            
            // Transaction-scoped payment (for same-transaction processing)
            // Use shorter key instead of full transaction hash (too long)
            string txPaymentKey = "tx_" + from.ToString() + "_" + marketId.ToString() + "_" + side;
            var txExistingPayment = pendingPaymentsMap.Get((ByteString)txPaymentKey);
            BigInteger txTotalPayment = txExistingPayment == null ? amount : (BigInteger)txExistingPayment + amount;
            pendingPaymentsMap.Put((ByteString)txPaymentKey, txTotalPayment);
            
            // User-scoped payment (for cross-transaction processing)
            string paymentKey = from.ToString() + "_" + marketId.ToString() + "_" + side;
            var existingPayment = pendingPaymentsMap.Get((ByteString)paymentKey);
            BigInteger totalPayment = existingPayment == null ? amount : (BigInteger)existingPayment + amount;
            pendingPaymentsMap.Put((ByteString)paymentKey, totalPayment);
        }

        // Contract deployment
        public static void _deploy(object data, bool update)
        {
            if (update) return;

            // Initialize market count
            Storage.Put(Storage.CurrentContext, MarketCountKey, 0);
        }

        // Update contract (owner only)
        public static void Update(ByteString nefFile, string manifest, object? data = null)
        {
            if (!IsOwner()) throw new Exception("No authorization.");
            ContractManagement.Update(nefFile, manifest, data);
        }

        // Destroy contract (owner only)
        public static void Destroy()
        {
            if (!IsOwner()) throw new Exception("No authorization.");
            ContractManagement.Destroy();
        }

        // ========== TEST FUNCTIONS FOR DEBUGGING ==========

        /// <summary>
        /// Test function to check contract state and permissions
        /// </summary>
        [DisplayName("testContractState")]
        public static string TestContractState()
        {
            UInt160 caller = Runtime.Transaction.Sender;
            BigInteger currentTime = Runtime.Time;
            UInt160 contractHash = Runtime.ExecutingScriptHash;
            BigInteger gasBalance = GAS.BalanceOf(contractHash);
            
            string result = "Contract State:\n";
            result += "Caller: " + caller.ToString() + "\n";
            result += "Current Time: " + currentTime.ToString() + "\n";
            result += "Contract Hash: " + contractHash.ToString() + "\n";
            result += "GAS Balance: " + gasBalance.ToString() + "\n";
            result += "Calling Script Hash: " + Runtime.CallingScriptHash.ToString() + "\n";
            
            return result;
        }

        /// <summary>
        /// Test function to check if buyYes can be called with given parameters
        /// Returns detailed status without actually executing the trade
        /// </summary>
        [DisplayName("testBuyYes")]
        public static string TestBuyYes(BigInteger marketId, BigInteger amount)
        {
            string result = "=== Test BuyYes ===\n";
            
            try
            {
                // Check amount
                if (amount <= 0)
                {
                    return result + "ERROR: Amount must be greater than 0\n";
                }
                result += "Amount: " + amount.ToString() + " (valid)\n";

                // Get market data
                MarketData market = GetMarket(marketId);
                if (market == null)
                {
                    return result + "ERROR: Market not found (ID: " + marketId.ToString() + ")\n";
                }
                result += "Market found: " + market.Question + "\n";

                // Check if resolved
                if (market.Resolved)
                {
                    return result + "ERROR: Market is already resolved\n";
                }
                result += "Market not resolved (OK)\n";

                // Check resolve date
                if (Runtime.Time >= market.ResolveDate)
                {
                    return result + "ERROR: Market resolve date has passed. Current: " + Runtime.Time.ToString() + ", Resolve: " + market.ResolveDate.ToString() + "\n";
                }
                result += "Resolve date check passed\n";

                // Check caller
                UInt160 caller = Runtime.Transaction.Sender;
                result += "Caller: " + caller.ToString() + "\n";

                // Check payment status
                StorageMap pendingPaymentsMap = new(Storage.CurrentContext, StringToBytes("pendingPay"));
                string paymentKey = caller.ToString() + "_" + marketId.ToString() + "_yes";
                // Use shorter key instead of full transaction hash (too long)
                string txPaymentKey = "tx_" + caller.ToString() + "_" + marketId.ToString() + "_yes";
                
                var txPaymentAmount = pendingPaymentsMap.Get((ByteString)txPaymentKey);
                var paymentAmount = pendingPaymentsMap.Get((ByteString)paymentKey);
                
                BigInteger availableAmount = 0;
                if (txPaymentAmount != null)
                    availableAmount = (BigInteger)txPaymentAmount;
                if (paymentAmount != null)
                    availableAmount += (BigInteger)paymentAmount;
                
                result += "Available payment: " + availableAmount.ToString() + "\n";
                result += "Required amount: " + amount.ToString() + "\n";

                if (availableAmount < amount)
                {
                    result += "WARNING: Insufficient payment. Will attempt GAS transfer.\n";
                    result += "GAS Contract Hash: " + GAS.Hash.ToString() + "\n";
                    result += "Contract Hash: " + Runtime.ExecutingScriptHash.ToString() + "\n";
                }
                else
                {
                    result += "Payment sufficient (OK)\n";
                }

                // Check GAS balance
                BigInteger contractGasBalance = GAS.BalanceOf(Runtime.ExecutingScriptHash);
                BigInteger callerGasBalance = GAS.BalanceOf(caller);
                result += "Contract GAS Balance: " + contractGasBalance.ToString() + "\n";
                result += "Caller GAS Balance: " + callerGasBalance.ToString() + "\n";

                result += "\n=== All checks passed ===\n";
                return result;
            }
            catch (Exception ex)
            {
                return result + "EXCEPTION: " + ex.Message + "\n";
            }
        }

        /// <summary>
        /// Test function to check GAS transfer capability
        /// </summary>
        [DisplayName("testGasTransfer")]
        public static string TestGasTransfer(BigInteger amount)
        {
            string result = "=== Test GAS Transfer ===\n";
            
            try
            {
                UInt160 caller = Runtime.Transaction.Sender;
                UInt160 contractHash = Runtime.ExecutingScriptHash;
                
                result += "Caller: " + caller.ToString() + "\n";
                result += "Contract: " + contractHash.ToString() + "\n";
                result += "Amount: " + amount.ToString() + "\n";
                
                // Check balances
                BigInteger callerBalance = GAS.BalanceOf(caller);
                BigInteger contractBalance = GAS.BalanceOf(contractHash);
                
                result += "Caller GAS Balance: " + callerBalance.ToString() + "\n";
                result += "Contract GAS Balance: " + contractBalance.ToString() + "\n";
                
                if (callerBalance < amount)
                {
                    return result + "ERROR: Insufficient caller balance\n";
                }
                
                // Try transfer (this will actually transfer, so use small amounts for testing)
                if (amount > 0 && amount <= 1000000) // Only allow small test amounts
                {
                    bool transferResult = SafeTransfer(GAS.Hash, caller, contractHash, amount, "test");
                    result += "Transfer result: " + transferResult.ToString() + "\n";
                    
                    BigInteger newContractBalance = GAS.BalanceOf(contractHash);
                    result += "New Contract Balance: " + newContractBalance.ToString() + "\n";
                }
                else
                {
                    result += "Skipping actual transfer (amount too large for test)\n";
                }
                
                result += "\n=== Test completed ===\n";
                return result;
            }
            catch (Exception ex)
            {
                return result + "EXCEPTION: " + ex.Message + "\n";
            }
        }

        /// <summary>
        /// Test function to check storage operations
        /// </summary>
        [DisplayName("testStorage")]
        public static string TestStorage(BigInteger marketId)
        {
            string result = "=== Test Storage ===\n";
            
            try
            {
                result += "Market ID: " + marketId.ToString() + "\n";
                
                // Test market retrieval
                MarketData market = GetMarket(marketId);
                if (market == null)
                {
                    return result + "ERROR: Market not found\n";
                }
                
                result += "Market Question: " + market.Question + "\n";
                result += "Market Resolved: " + market.Resolved.ToString() + "\n";
                result += "Yes Shares: " + market.YesShares.ToString() + "\n";
                result += "No Shares: " + market.NoShares.ToString() + "\n";
                
                // Test storage read
                StorageMap yesSharesMap = new(Storage.CurrentContext, YesSharesPrefix);
                var yesSharesValue = yesSharesMap.Get((ByteString)marketId);
                BigInteger yesShares = yesSharesValue is null ? 0 : (BigInteger)yesSharesValue;
                result += "Storage Yes Shares: " + yesShares.ToString() + "\n";
                
                // Test storage write (increment by 1 for test)
                yesShares += 1;
                yesSharesMap.Put((ByteString)marketId, yesShares);
                result += "Storage write test: OK\n";
                
                // Verify write
                var verifyValue = yesSharesMap.Get((ByteString)marketId);
                BigInteger verifyShares = verifyValue is null ? 0 : (BigInteger)verifyValue;
                result += "Verified Shares: " + verifyShares.ToString() + "\n";
                
                // Revert test change
                yesShares -= 1;
                yesSharesMap.Put((ByteString)marketId, yesShares);
                
                result += "\n=== Storage test passed ===\n";
                return result;
            }
            catch (Exception ex)
            {
                return result + "EXCEPTION: " + ex.Message + "\n";
            }
        }

        /// <summary>
        /// Simple test function that just returns success
        /// </summary>
        [DisplayName("testSimple")]
        public static string TestSimple()
        {
            return "Test function called successfully! Contract is working.";
        }
    }

    // Market data structure
    public class MarketData
    {
        public string? Id;
        public string? Question;
        public string? Description;
        public string? Category;
        public BigInteger ResolveDate;
        public string? OracleUrl;
        public UInt160? Creator;
        public BigInteger CreatedAt;
        public bool Resolved;
        public bool Outcome;
        public BigInteger YesShares;
        public BigInteger NoShares;
    }
}

