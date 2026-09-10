# BizXtreme Game Dashboard / Persistence / P2P Integration

Chimera II OS remains the platform integration layer for BizXtreme clients.

## Dashboard

The shared dashboard vocabulary is: score, XP, expedition progress, play time, peer count and rank. Aurora visual styling uses the same glass/neon language as the Chimera II Aurora Web UI.

## Persistent game state

Browser clients persist a versioned save snapshot locally. Unity clients persist an equivalent JSON snapshot. Native Chimera clients should use the OS VFS/application-data layer and retain the same schema fields.

## Hall of Fame

Local records are valid for offline play. Competitive global records must be validated by a trusted service or platform. A P2P peer is not an authority for another peer's score.

## P2P networking

WebRTC/RTCDataChannel is appropriate for browser peer-to-peer game/chat transport. Connection setup still needs signaling and ICE/STUN/TURN infrastructure. The signaling component is intentionally separate from the game data channel.

The peer-discovery model is opt-in. Chimera/BizXtreme clients must not scan the public Internet or maintain a raw-IP database of players. Directory records use pseudonymous peer IDs and optional network hints; raw IP retention is outside the client contract.

## Splash / asset pipeline

The Aurora Frontier splash is a derived composite from Library artwork. Client code references a stable logical asset ID and platform-specific loaders. Release packaging should place the PNG into the corresponding resource bundle before production builds.

## Security and privacy

- No raw private keys or wallet seeds in game save files.
- No public-Internet device scanning.
- No silent collection of player IP addresses.
- Peer-to-peer connections use the platform's encrypted transport mechanisms.
- User discovery requires explicit opt-in.
