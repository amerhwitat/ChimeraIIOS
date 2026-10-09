package chimera.drivers.acquisition;

import java.net.URI;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

public final class AcquisitionPolicy {
    public static final long DEFAULT_MAX_DOWNLOAD_BYTES = 512L * 1024L * 1024L;

    private final Set<String> allowedHosts;
    private final String kernelAbi;
    private final boolean requireSignature;
    private final long maxDownloadBytes;

    public AcquisitionPolicy(Set<String> allowedHosts, String kernelAbi, boolean requireSignature) {
        this(allowedHosts, kernelAbi, requireSignature, DEFAULT_MAX_DOWNLOAD_BYTES);
    }

    public AcquisitionPolicy(Set<String> allowedHosts, String kernelAbi, boolean requireSignature, long maxDownloadBytes) {
        if (allowedHosts == null || allowedHosts.isEmpty()) {
            throw new IllegalArgumentException("at least one allowed driver source host is required");
        }
        if (maxDownloadBytes < 1) throw new IllegalArgumentException("max download size must be positive");
        this.allowedHosts = allowedHosts.stream()
            .map(host -> host.toLowerCase(Locale.ROOT))
            .collect(Collectors.toUnmodifiableSet());
        this.kernelAbi = kernelAbi;
        this.requireSignature = requireSignature;
        this.maxDownloadBytes = maxDownloadBytes;
    }

    public long maxDownloadBytes() { return maxDownloadBytes; }

    public void validate(DriverArtifact artifact) {
        if (artifact == null) throw new IllegalArgumentException("driver artifact is required");
        URI uri;
        try {
            uri = URI.create(artifact.url());
        } catch (RuntimeException e) {
            throw new IllegalArgumentException("invalid driver source URL", e);
        }
        if (!"https".equalsIgnoreCase(uri.getScheme())) throw new IllegalArgumentException("driver sources must use HTTPS");
        if (uri.getHost() == null || !allowedHosts.contains(uri.getHost().toLowerCase(Locale.ROOT))) {
            throw new IllegalArgumentException("driver source is not allowlisted");
        }
        if (!artifact.sha256().matches("[0-9a-fA-F]{64}")) throw new IllegalArgumentException("invalid SHA-256 metadata");
        if (requireSignature && !artifact.signed()) throw new IllegalArgumentException("driver artifact is not trusted/signed");
        if ("linux".equalsIgnoreCase(artifact.platform()) && "kernel-module".equalsIgnoreCase(artifact.packageType())
                && (kernelAbi == null || !kernelAbi.equals(artifact.kernelAbi()))) {
            throw new IllegalArgumentException("Linux kernel module ABI does not match Chimera");
        }
        if ("windows".equalsIgnoreCase(artifact.platform())
                && !Set.of("inf", "driver-package").contains(artifact.packageType().toLowerCase(Locale.ROOT))) {
            throw new IllegalArgumentException("unsupported Windows driver package type");
        }
    }
}
