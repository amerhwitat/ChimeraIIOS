package chimera.drivers.acquisition;

import chimera.drivers.hardware.HardwareId;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

public final class DriverAcquisitionManager {
    private final AcquisitionPolicy policy;

    public DriverAcquisitionManager(AcquisitionPolicy policy) { this.policy = policy; }

    public boolean matches(DriverArtifact artifact, HardwareId device) {
        return artifact.hardwareIds().stream().anyMatch(id -> id.matches(device));
    }

    public DriverAcquisitionResult stage(Path downloaded, DriverArtifact artifact, Path destination) throws IOException {
        policy.validate(artifact);
        if (!verifySha256(downloaded, artifact.sha256())) return DriverAcquisitionResult.rejected("SHA-256 verification failed");
        Files.createDirectories(destination);
        Path target = destination.resolve(downloaded.getFileName());
        Files.copy(downloaded, target, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        return new DriverAcquisitionResult(true, target, "verified and staged; installation remains a separate authorized operation");
    }

    public static boolean verifySha256(Path file, String expected) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream in = Files.newInputStream(file)) {
                byte[] buffer = new byte[1024 * 1024];
                for (int read; (read = in.read(buffer)) != -1;) digest.update(buffer, 0, read);
            }
            return HexFormat.of().formatHex(digest.digest()).equalsIgnoreCase(expected);
        } catch (java.security.NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
