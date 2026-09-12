$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } elseif ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }

function Need([string]$cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Host "Android SDK: $Sdk"
if (-not (Test-Path (Join-Path $Sdk 'platform-tools'))) {
  Write-Warning 'Android SDK is not installed. Run install-android-sdk.ps1 first.'
  & (Join-Path $Root 'install-android-sdk.ps1')
}

if (-not (Need 'java')) { throw 'JDK 17+ is required. Install/configure JAVA_HOME.' }
$SdkManager = Join-Path $Sdk 'cmdline-tools\latest\bin\sdkmanager.bat'
if (Test-Path $SdkManager) {
  & $SdkManager "platform-tools" "platforms;android-36" "build-tools;36.0.0"
}

$Gradle = Join-Path $Root 'gradlew.bat'
if (-not (Test-Path $Gradle)) { throw 'Gradle wrapper missing. Generate it from a Gradle-enabled Android project or run from Android Studio.' }
Push-Location $Root
try { & $Gradle --no-daemon clean assembleDebug assembleRelease } finally { Pop-Location }
Write-Host 'APK build completed. Inspect app/build/outputs/apk/.'
