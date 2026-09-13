namespace Chimera.Desktop;
public enum ChimeraDirection { Ltr, Rtl }
public readonly record struct ChimeraLocale(string Id, string Language, string Script, ChimeraDirection Direction) {
  public static ChimeraLocale For(string? id) => id?.StartsWith("ar", System.StringComparison.OrdinalIgnoreCase) == true ? new("ar-SA","ar","Arabic",ChimeraDirection.Rtl) : new("en-US","en","Latin",ChimeraDirection.Ltr);
}
