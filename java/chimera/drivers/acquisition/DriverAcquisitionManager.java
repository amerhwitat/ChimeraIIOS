package chimera.drivers.acquisition;

import chimera.drivers.hardware.HardwareId;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.HexFormat;

public final class DriverAcquisitionManager {
    private final AcquisitionPolicy policy;
    /* Redirects are disabled so an allowlisted HTTPS URL cannot redirect to an untrusted host. */
    private final HttpClient http = HttpClient.newBuilder()
        .followRedirects(HttpClient.Redirect.NEVER)
        .connectTimeout(java.time.Duration.ofSeconds(15))
        .build();

    public DriverAcquisitionManager(AcquisitionPolicy policy) {
        if (policy == null) throw new IllegalArgumentException("acquisition policy is required");
        this.policy = policy;
    }

    public boolean matches(DriverArtifact artifact, HardwareId device) {
        return artifact != null && device != null
            && artifact.hardwareIds().stream().anyMatch(id -> id.matches(device));
    }

    public Path acquire(DriverArtifact artifact, Path destination) throws IOException, InterruptedException {
        policy.validate(artifact);
        URI uri = URI.create(artifact.url());
        Path fileName = Path.of(uri.getPath()).getFileName();
        if (fileName == null || fileName.toString().isBlank() || fileName.toString().equals(".") || fileName.toString().equals("..")) {
            throw new IOException("artifact URL has no safe filename");
        }

        Path root = destination.toAbsolutePath().normalize();
        Files.createDirectories(root);
        Path target = root.resolve(fileName.toString()).normalize();
        if (!root.equals(target.getParent())) {
            throw new IOException("artifact filename escaped destination directory");
        }
        Path temporary = Files.createTempFile(root, ".chimera-download-", ".part");
        boolean moved = false;
        try {
            HttpRequest request = HttpRequest.newBuilder(uri)
                .timeout(java.time.Duration.ofMinutes(2))
                .header("User-Agent", "ChimeraIIOS-DriverBroker/1")
                .GET()
                .build();
            HttpResponse<InputStream> response = http.send(request, HttpResponse.BodyHandlers.ofInputStream());
            try (InputStream input = response.body()) {
                if (response.statusCode() / 100 != 2) {
                    throw new IOException("driver source returned HTTP status " + response.statusCode()
                        + "; redirects and non-success responses are not followed");
                }
                long total = 0;
                byte[] buffer = new byte[64 * 1024];
                try (var output = Files.newOutputStream(temporary)) {
                    for (int read; (read = input.read(buffer)) != -1;) {
                        total += read;
                        if (total > policy.maxDownloadBytes()) {
                            throw new IOException("driver download exceeds configured size limit");
                        }
                        output.write(buffer, 0, read);
                    }
                }
            }
            if (!verifySha256(temporary, artifact.sha256())) {
                throw new IOException("driver SHA-256 verification failed");
            }
            try {
                Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING);
            }
            moved = true;
            return target;
        } finally {
            if (!moved) Files.deleteIfExists(temporary);
        }
    }

    public DriverAcquisitionResult stage(Path downloaded, DriverArtifact artifact, Path destination) throws IOException {
        policy.validate(artifact);
        if (!verifySha256(downloaded, artifact.sha256())) return DriverAcquisitionResult.rejected("SHA-256 verification failed");
        Files.createDirectories(destination);
        Path target = destination.resolve(downloaded.getFileName());
        Files.copy(downloaded, target, StandardCopyOption.REPLACE_EXISTING);
        return new DriverAcquisitionResult(true, target, "verified and staged; installation remains a separate authorized operation");
    }

    public static boolean verifySha256(Path file, String expected) throws IOException {
        if (file == null || expected == null || !expected.matches("[0-9a-fA-F]{64}")) return false;
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
