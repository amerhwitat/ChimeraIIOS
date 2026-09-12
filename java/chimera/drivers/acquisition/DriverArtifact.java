package chimera.drivers.acquisition;

import chimera.drivers.hardware.HardwareId;
import java.util.List;

public record DriverArtifact(
    String name,
    String platform,
    String packageType,
    String url,
    String sha256,
    List<HardwareId> hardwareIds,
    boolean signed,
    String kernelAbi,
    String licenseSpdx,
    String sourceUrl) {}
