package chimera.drivers.hardware;

import java.util.Locale;

public record HardwareId(String bus, String vendor, String device, String subsystem) {
    public HardwareId {
        if (bus == null || vendor == null || device == null) throw new IllegalArgumentException("hardware id fields required");
    }

    public boolean matches(HardwareId candidate) {
        if (candidate == null) return false;
        return bus.equalsIgnoreCase(candidate.bus)
            && vendor.equalsIgnoreCase(candidate.vendor)
            && device.equalsIgnoreCase(candidate.device)
            && (subsystem == null || subsystem.equalsIgnoreCase(candidate.subsystem == null ? "" : candidate.subsystem));
    }

    public String normalized() {
        return String.join(":", bus.toLowerCase(Locale.ROOT), vendor.toLowerCase(Locale.ROOT), device.toLowerCase(Locale.ROOT));
    }
}
