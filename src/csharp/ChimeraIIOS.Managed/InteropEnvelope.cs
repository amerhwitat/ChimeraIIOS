namespace ChimeraIIOS.Managed;

public sealed record InteropEnvelope(string Schema, int Version, string Operation, object? Payload)
{
    public static InteropEnvelope Create(string operation, object? payload = null) =>
        new("chimera.os.interop", 1, operation, payload);
}
