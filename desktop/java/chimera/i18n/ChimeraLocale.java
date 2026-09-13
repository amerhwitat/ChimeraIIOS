package chimera.i18n;
public final class ChimeraLocale {
  public enum Direction { LTR, RTL }
  public final String id, language, script; public final Direction direction;
  public ChimeraLocale(String id, String language, String script, Direction direction) { this.id=id; this.language=language; this.script=script; this.direction=direction; }
  public static ChimeraLocale forId(String id) { return id != null && id.toLowerCase().startsWith("ar") ? new ChimeraLocale("ar-SA","ar","Arabic",Direction.RTL) : new ChimeraLocale("en-US","en","Latin",Direction.LTR); }
}
