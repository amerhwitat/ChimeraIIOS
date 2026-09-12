package io.chimera.p2p;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/** Canonical P2P integrity helper; authentication is supplied by the transport. */
public final class ChimeraP2PEnvelope {
    private ChimeraP2PEnvelope() {}

    public static String sha256(String payload) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(payload.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder(64);
            for (byte b : digest) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
