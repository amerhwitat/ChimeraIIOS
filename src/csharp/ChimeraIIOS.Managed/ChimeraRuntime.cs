namespace ChimeraIIOS.Managed;

public static class ChimeraRuntime
{
    public static InteropEnvelope Health() => InteropEnvelope.Create("health", new
    {
        runtime = Environment.Version.ToString(),
        os = Environment.OSVersion.VersionString,
        processArchitecture = System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture.ToString()
    });
}
