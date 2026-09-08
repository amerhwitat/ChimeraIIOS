using UnrealBuildTool;

public class AuroraDesktop : ModuleRules
{
    public AuroraDesktop(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "Slate", "SlateCore", "UMG" });

        if (Target.Platform == UnrealTargetPlatform.Linux)
        {
            PublicDefinitions.Add("AURORA_USE_WAYLAND=1");
            PublicSystemLibraries.Add("wayland-client");
        }
    }
}
