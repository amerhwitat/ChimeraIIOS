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
        if (!manager.matches(artifact, id)) throw new AssertionError("hardware match failed");
        Path input = Files.createTempFile("chimera-driver", ".bin");
        Files.writeString(input, "chimera");
        Path output = Files.createTempDirectory("chimera-stage");
        if (!manager.stage(input, artifact, output).accepted()) throw new AssertionError("staging failed");
        System.out.println("Java driver acquisition tests passed");
    }

    private static String sha256(String value) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value.getBytes()));
    }
}
