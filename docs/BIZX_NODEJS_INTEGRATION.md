# BizX / BizXtreme Node.js integration

BizX and BizXtreme now provide Node.js implementations under language-specific `nodejs/` trees. Chimera II OS integration should consume these implementations through stable API boundaries rather than coupling the kernel or native components to JavaScript source.

## Integration boundary

- BizX: core business services and wallet/provider abstractions.
- BizXtreme: extended services including WebGL/Three.js, crypto, game, Aurora and Chimera-facing adapters.
- Chimera II OS: host/runtime integration, service orchestration, networking and native acceleration.

The Node.js layer is intended for user-space services and web/API integration; performance-critical kernel/native operations remain in the appropriate native-language implementation.
