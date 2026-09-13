# Security policy

Never commit private keys, passwords, seed phrases, tokens or production credentials. Network and routing control-plane configuration is privileged.

Remote application networking requires authenticated/encrypted transport where supported. Dynamic routing and SDN changes require explicit OS capabilities, authenticated control channels and versioned configuration.

Uploaded avatars are untrusted files: allow only configured image MIME types, enforce byte/pixel limits, decode and normalize before rendering, and remove unnecessary metadata.

Application profiles must not contain raw IP addresses or exact location. Secrets must remain in the platform secret store and outside logs, telemetry, save files and P2P messages.
