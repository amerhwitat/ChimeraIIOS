package chimera.drivers.acquisition;

import chimera.drivers.hardware.HardwareId;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

public final class DriverAcquisitionManager {
    private final AcquisitionPolicy policy;
    private final HttpClient http = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build();

    public DriverAcquisitionManager(AcquisitionPolicy policy) { this.policy = policy; }

    public boolean matches(DriverArtifact artifact, HardwareId device) {
        return artifact.hardwareIds().stream().anyMatch(id -> id.matches(device));
    }

    public Path acquire(DriverArtifact artifact, Path destination) throws IOException, InterruptedException {
        policy.validate(artifact);
        URI uri = URI.create(artifact.url());
        Path target = destination.resolve(Path.of(uri.getPath()).getFileName().toString());
        Files.createDirectories(destination);
        HttpRequest request = HttpRequest.newBuilder(uri).header("User-Agent", "ChimeraIIOS-DriverBroker/1").GET().build();
        HttpResponse<Path> response = http.send(request, HttpResponse.BodyHandlers.ofFile(target));
        if (response.statusCode() / 100 != 2 || !verifySha256(target, artifact.sha256())) {
            Files.deleteIfExists(target);
            throw new IOException("driver acquisition failed verification or HTTP status: " + response.statusCode());
        }
        return target;
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
