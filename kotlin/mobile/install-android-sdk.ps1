$ErrorActionPreference = 'Stop'
$Sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } elseif ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$Tools = Join-Path $Sdk 'cmdline-tools\latest'
$Zip = Join-Path $env:TEMP 'android-commandlinetools.zip'
$Url = 'https://dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip'

New-Item -ItemType Directory -Force -Path $Sdk | Out-Null
if (-not (Test-Path (Join-Path $Tools 'bin\sdkmanager.bat'))) {
  Write-Host "Downloading Android Command-line Tools..."
  Invoke-WebRequest -Uri $Url -OutFile $Zip
  $Stage = Join-Path $env:TEMP 'android-cmdline-stage'
  Remove-Item $Stage -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force -Path $Stage | Out-Null
  Expand-Archive $Zip -DestinationPath $Stage -Force
  New-Item -ItemType Directory -Force -Path $Tools | Out-Null
  Copy-Item (Join-Path $Stage 'cmdline-tools\*') $Tools -Recurse -Force
}
$SdkManager = Join-Path $Tools 'bin\sdkmanager.bat'
& $SdkManager --sdk_root=$Sdk --licenses
& $SdkManager --sdk_root=$Sdk "platform-tools" "platforms;android-36" "build-tools;36.0.0"
[Environment]::SetEnvironmentVariable('ANDROID_SDK_ROOT',$Sdk,'User')
[Environment]::SetEnvironmentVariable('ANDROID_HOME',$Sdk,'User')
Write-Host "Android SDK installed/configured at $Sdk"
