package chimera.drivers.acquisition;

import chimera.drivers.hardware.HardwareId;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;

public final class DriverAcquisitionManagerTest {
    public static void main(String[] args) throws Exception {
        HardwareId id = new HardwareId("pci", "8086", "1234", null);
        DriverArtifact artifact = new DriverArtifact("demo", "linux", "source", "https://kernel.org/demo", sha256("chimera"), List.of(id), true, null, "GPL-2.0-only", "https://kernel.org/");
        AcquisitionPolicy policy = new AcquisitionPolicy(Set.of("kernel.org"), null, true);
        DriverAcquisitionManager manager = new DriverAcquisitionManager(policy);
        if (policy.maxDownloadBytes() != AcquisitionPolicy.DEFAULT_MAX_DOWNLOAD_BYTES) {
            throw new AssertionError("default download limit mismatch");
        }
        AcquisitionPolicy bounded = new AcquisitionPolicy(Set.of("kernel.org"), null, true, 7);
        if (bounded.maxDownloadBytes() != 7) throw new AssertionError("custom download limit mismatch");
        try {
            new AcquisitionPolicy(Set.of(), null, true);
            throw new AssertionError("empty host allowlist must be rejected");
        } catch (IllegalArgumentException expected) {
            // Expected: no sources may be fetched without an explicit host allowlist.
        }
        try {
            bounded.validate(new DriverArtifact("bad", "linux", "source", "https://evil.example/file",
                sha256("chimera"), List.of(id), true, null, "GPL-2.0-only", "https://kernel.org/"));
            throw new AssertionError("non-allowlisted host must be rejected");
        } catch (IllegalArgumentException expected) {
            // Expected: the URL host must be explicitly allowlisted.
        }
        if (!manager.matches(artifact, id)) throw new AssertionError("hardware match failed");
        Path input = Files.createTempFile("chimera-driver", ".bin");
        Files.writeString(input, "chimera");
        Path output = Files.createTempDirectory("chimera-stage");
        if (!manager.stage(input, artifact, output).accepted()) throw new AssertionError("staging failed");
        if (DriverAcquisitionManager.verifySha256(input, "0".repeat(64))) {
            throw new AssertionError("incorrect digest must fail verification");
        }
        System.out.println("Java driver acquisition tests passed");
    }

    private static String sha256(String value) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes()));
    }
}
