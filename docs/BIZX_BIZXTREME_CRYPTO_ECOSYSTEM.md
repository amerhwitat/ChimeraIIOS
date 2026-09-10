# BizX / BizXtreme Crypto Ecosystem Integration

Chimera II OS integration now defines a provider-neutral crypto application boundary for BizX and BizXtreme.

## Components

- wallet-provider adapters for external signing;
- public balance readers;
- chain transaction scanners;
- explorer URL registry;
- transaction verification;
- game commerce and entitlement references;
- Unity C#/WebGL integration source maintained in BizXtreme.

## Chain strategy

The ecosystem supports an extensible set of reference chain families including Bitcoin, EVM networks, Solana/SPL, Litecoin, Dogecoin, Bitcoin Cash, XRP, Cardano, Polkadot, TRON, Stellar and TON. "All coins" is treated as an adapter architecture: thousands of tokens can be represented through token metadata on a supported chain, while fundamentally different chains require their own protocol adapter.

## Security

Wallet signing remains provider-side. No Chimera service should request a seed phrase or private key merely to connect, read balances, scan transactions, or pay for a game item. Secrets must not enter logs, telemetry, source control or server databases.

## Commerce

Game purchases use public transaction references and confirmation rules. Entitlements and physical accessory fulfillment are activated only after independent payment verification.

## WebGL

The Unity integration uses the browser JavaScript bridge documented by Unity. Browser wallet APIs are accessed from a `.jslib` adapter and exposed to C# through WebGL interop. citeturn0search3turn0search7

## Research/audit status

Packaged applications in external repositories are not treated as source code. Binary reverse engineering requires the actual binary artifact and produces an audit report separate from the clean-room integration layer.
