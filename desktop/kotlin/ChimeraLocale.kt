package chimera.desktop

enum class Direction { LTR, RTL }
data class ChimeraLocale(val id: String, val language: String, val script: String, val direction: Direction) {
  companion object { fun forId(id: String?) = if (id?.startsWith("ar", true) == true) ChimeraLocale("ar-SA","ar","Arabic",Direction.RTL) else ChimeraLocale("en-US","en","Latin",Direction.LTR) }
}
