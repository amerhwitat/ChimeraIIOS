package com.amerhwitat.chimera.apple

/** Stable Kotlin/Native boundary consumed by the Swift/Xcode layer. */
class SharedKit {
    fun schemaVersion(): Int = 1
    fun platformContract(): String = "Chimera Apple shared contract"
}
