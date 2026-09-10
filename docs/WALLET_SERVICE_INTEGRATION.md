# Chimera II wallet service integration

Chimera II wallet services provide controlled blockchain observation and owner-authorized transaction submission.

## Service layers

- **Wallet API:** balances, receiving addresses, transaction construction and status.
- **Signer boundary:** external signer, hardware wallet, OS wallet, or authenticated node wallet.
- **Spotnik/network layer:** RPC transport and broadcast.
- **Nucleus:** normalized address, balance, transaction and confirmation records.
- **Aurora/Web UI:** explicit transaction review and confirmation before broadcast.

## Ethereum

The service can broadcast an externally signed transaction through `eth_sendRawTransaction`. Private keys are not passed to the broadcast API.

## Bitcoin

The service can request receiving addresses and submit spend requests through an authenticated Bitcoin Core wallet. RPC credentials belong in protected configuration, never source control.

## Fund classification

Every observed address/output is classified as `OWNED`, `WATCH_ONLY`, `BURN`, or `UNKNOWN`. Only `OWNED` funds are eligible for spending workflows. `BURN` funds are tracked for accounting but are never represented as recoverable.

## Required transaction controls

Before broadcast, the service should verify network/chain, recipient, amount, fee, nonce or UTXO set, source ownership, and user confirmation. After broadcast it records the transaction hash and confirmation lifecycle.

## Security boundary

Wallet cracking, private-key guessing, seed enumeration, credential harvesting and unauthorized fund movement remain outside the Chimera II design.
