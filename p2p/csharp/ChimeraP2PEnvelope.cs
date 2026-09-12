namespace Chimera.P2P;

public sealed record ChimeraP2PEnvelope(
    int Version,
    string Type,
    string NodeId,
    long Sequence,
    string PayloadHash,
    object Payload,
    string[]? Capabilities = null,
    string? Signature = null);

public static class ChimeraP2PIntegrity
{
    public static string Sha256(string text)
    {
        using var sha = System.Security.Cryptography.SHA256.Create();
        var bytes = sha.ComputeHash(System.Text.Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
