package chimera.drivers.acquisition;

import java.nio.file.Path;

public record DriverAcquisitionResult(boolean accepted, Path stagedPath, String message) {
    public static DriverAcquisitionResult rejected(String message) { return new DriverAcquisitionResult(false, null, message); }
}
