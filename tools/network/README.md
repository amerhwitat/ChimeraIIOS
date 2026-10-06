# Chimera II Network Signaling Relay

This is the optional local/client-server WebSocket relay used by the Network Hub and Game Center. WebRTC still performs the peer-to-peer connection; the relay only introduces peers and forwards signaling messages.

Install and run:

```sh
cd tools/network
npm install
npm start
```

The default endpoint is `ws://127.0.0.1:8780`. Set `CHIMERA_SIGNAL_HOST` and `CHIMERA_SIGNAL_PORT` when deploying behind an authorized reverse proxy.

The implementation uses the open-source **ws** Node.js WebSocket server library.