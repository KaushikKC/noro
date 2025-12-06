# PredictX Neo Smart Contract

This directory contains the Neo N3 smart contract for the PredictX prediction market platform.

## Contract Overview

The `PredictXMarket` contract implements a decentralized prediction market system on the Neo blockchain with the following features:

- **Market Creation**: Create new prediction markets with questions, descriptions, categories, and resolve dates
- **Trading**: Buy YES or NO shares using GAS tokens
- **Oracle Integration**: Request and handle oracle callbacks for market resolution
- **Payouts**: Distribute winnings to holders of winning shares
- **Query Functions**: Get market data and current probability

## Contract Methods

### Market Management
- `createMarket(question, description, category, resolveDate, oracleUrl)` - Create a new prediction market
- `getMarket(marketId)` - Get market data by ID
- `getMarketCount()` - Get total number of markets created

### Trading
- `buyYes(marketId, amount)` - Buy YES shares for a market
- `buyNo(marketId, amount)` - Buy NO shares for a market
- `getProbability(marketId)` - Get current YES probability (0-10000, where 10000 = 100%)

### Oracle & Resolution
- `requestResolve(marketId, oracleUrl, filter, callbackMethod)` - Request oracle resolution
- `onOracleCallback(requestId, result, userData)` - Handle oracle callback (oracle-only)

### Payouts
- `payout(marketId)` - Distribute payouts to winners

### Events
- `MarketCreated(marketId, question, category, resolveDate, oracleUrl)`
- `TradeExecuted(marketId, trader, isYes, amount)`
- `MarketResolved(marketId, outcome)`
- `PayoutDistributed(marketId, recipient, amount)`

## Development Setup

### Prerequisites
- [Neo Blockchain Toolkit](https://marketplace.visualstudio.com/items?itemName=NeoResearch.neo-blockchain-toolkit) for Visual Studio Code
- Neo N3 SDK (included in the toolkit)
- .NET SDK 6.0 or later

### Building the Contract

1. Install Neo Blockchain Toolkit extension in VS Code
2. Open the contract file in VS Code
3. Build the contract using the Neo extension commands
4. The contract will compile to a `.nef` file

### Deployment

1. Deploy to Neo TestNet using Neo-CLI or Neo-GUI
2. Update the `Owner` address in the contract with your wallet address
3. Deploy the contract and note the contract script hash
4. Update frontend/backend with the contract hash

### Testing

Use Neo-CLI or Neo-GUI to test contract methods:
- Invoke `createMarket` to create a test market
- Invoke `buyYes`/`buyNo` to trade
- Invoke `getMarket` and `getProbability` to query data

## Contract Properties

- **Owner**: Contract owner address (update before deployment)
- **Storage Prefixes**: Used for organizing storage data
- **Market Count**: Tracks total number of markets

## Important Notes

1. **Owner Address**: Update the `Owner` constant with your actual wallet address before deployment
2. **Oracle Integration**: The contract uses Neo's native Oracle service
3. **GAS Tokens**: All trading uses Neo's native GAS token
4. **Storage**: Market data and user shares are stored on-chain
5. **Payout Logic**: Current implementation is simplified - production version should iterate through all holders

## Security Considerations

- All inputs are validated
- Access control via `IsOwner()` for admin functions
- Oracle callbacks are restricted to Oracle contract only
- Market resolution requires resolve date to pass
- Trading is disabled after market resolution

## Next Steps

1. Update owner address
2. Deploy to Neo TestNet
3. Test all contract methods
4. Integrate with frontend via NeoLine wallet
5. Connect backend to contract via Neo SDK

