namespace Chimera.Sdk;
public static class ChimeraRuntime {
 public const string Version="1.0.0";
 public static string TargetTriple() => System.Runtime.InteropServices.RuntimeInformation.ProcessArchitecture switch {
 System.Runtime.InteropServices.Architecture.X64=>"chimera-x86_64",
 System.Runtime.InteropServices.Architecture.Arm64=>"chimera-aarch64", _=>"chimera-host"};
}
