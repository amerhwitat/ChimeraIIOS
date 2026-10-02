package chimera.runtime;

/** Common Java-side configuration and native bridge metadata. */
public final class ChimeraRuntime {
    private ChimeraRuntime() {}
    public static final int LOGICAL_BITS = Integer.getInteger("chimera.logical.bits", 8192);
    public static String root() { return System.getenv().getOrDefault("CHIMERA_ROOT", "."); }
}
