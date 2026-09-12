plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android { namespace = "com.amerhwitat.chimera.mobile"; compileSdk = 36; defaultConfig { applicationId = "com.amerhwitat.chimera.mobile"; minSdk = 26; targetSdk = 36; versionCode = 1; versionName = "0.1.0" }; buildTypes { release { isMinifyEnabled = false } } }
kotlin { jvmToolchain(17) }
