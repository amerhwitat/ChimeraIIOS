$ErrorActionPreference='Stop'
$sdk=$env:ANDROID_SDK_ROOT; if([string]::IsNullOrWhiteSpace($sdk)){$sdk=$env:ANDROID_HOME}; if([string]::IsNullOrWhiteSpace($sdk)){$sdk=Join-Path $HOME 'Android\Sdk'}
New-Item -ItemType Directory -Force -Path $sdk | Out-Null
$androidCli=Get-Command android -ErrorAction SilentlyContinue
$sdkmanager=Join-Path $sdk 'cmdline-tools\latest\bin\sdkmanager.bat'
if(-not (Test-Path $sdkmanager) -and -not $androidCli){$tmp=Join-Path $env:TEMP 'android-cli-install.cmd'; Invoke-WebRequest 'https://dl.google.com/android/cli/latest/windows_x86_64/install.cmd' -OutFile $tmp; & cmd /c $tmp}
if(Test-Path $sdkmanager){& $sdkmanager --sdk_root=$sdk --install 'platform-tools' 'platforms;android-36' 'build-tools;36.0.0'}
[Environment]::SetEnvironmentVariable('ANDROID_SDK_ROOT',$sdk,'User'); [Environment]::SetEnvironmentVariable('ANDROID_HOME',$sdk,'User'); $env:ANDROID_SDK_ROOT=$sdk; $env:ANDROID_HOME=$sdk
Write-Host "Android SDK ready: $sdk"
