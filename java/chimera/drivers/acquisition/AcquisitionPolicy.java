package chimera.drivers.acquisition;

import java.net.URI;
import java.util.Set;

public final class AcquisitionPolicy {
    private final Set<String> allowedHosts;
    private final String kernelAbi;
    private final boolean requireSignature;

    public AcquisitionPolicy(Set<String> allowedHosts, String kernelAbi, boolean requireSignature) {
        this.allowedHosts = Set.copyOf(allowedHosts);
        this.kernelAbi = kernelAbi;
        this.requireSignature = requireSignature;
    }

    public void validate(DriverArtifact artifact) {
        URI uri = URI.create(artifact.url());
        if (!"https".equalsIgnoreCase(uri.getScheme())) throw new IllegalArgumentException("driver sources must use HTTPS");
        if (!allowedHosts.contains(uri.getHost())) throw new IllegalArgumentException("driver source is not allowlisted");
        if (!artifact.sha256().matches("[0-9a-fA-F]{64}")) throw new IllegalArgumentException("invalid SHA-256 metadata");
        if (requireSignature && !artifact.signed()) throw new IllegalArgumentException("driver artifact is not trusted/signed");
        if ("linux".equalsIgnoreCase(artifact.platform()) && "kernel-module".equalsIgnoreCase(artifact.packageType())
                && (kernelAbi == null || !kernelAbi.equals(artifact.kernelAbi()))) {
            throw new IllegalArgumentException("Linux kernel module ABI does not match Chimera");
        }
        if ("windows".equalsIgnoreCase(artifact.platform())
                && !Set.of("inf", "driver-package").contains(artifact.packageType().toLowerCase())) {
            throw new IllegalArgumentException("unsupported Windows driver package type");
        }
    }
}
