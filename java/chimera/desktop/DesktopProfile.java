package chimera.desktop;

public record DesktopProfile(Platform platform, String name, boolean menuBar, boolean gestures, boolean accessibility) {
    public enum Platform { LINUX_GTK, LINUX_QT, WINDOWS_WIN32, WINDOWS_MODERN, MACOS_APPKIT, MACOS_SWIFTUI, CLASSIC }
    public static DesktopProfile of(Platform p) {
        return new DesktopProfile(p, p.name().toLowerCase().replace('_','-'), p != Platform.CLASSIC, p != Platform.CLASSIC, true);
    }
}
