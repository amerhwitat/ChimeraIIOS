package org.chimera.sdk;
public final class ChimeraRuntime {
 private ChimeraRuntime(){}
 public static String version(){return "1.0.0";}
 public static String targetTriple(){String a=System.getProperty("os.arch","");if(a.equals("amd64")||a.equals("x86_64"))return "chimera-x86_64";if(a.equals("aarch64"))return "chimera-aarch64";return "chimera-host";}
}
