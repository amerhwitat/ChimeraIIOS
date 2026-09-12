$ErrorActionPreference='Stop'
$repos=@('BizX','BizXtreme','ChimeraIIOS','CPU4096','CPU4096Simulator','PDFreaderPY','nlp','eth-key-check','bruteforce','keygen','test','general','VanG')
$root=Join-Path $PSScriptRoot 'workspace'; New-Item -ItemType Directory -Force -Path $root | Out-Null
& (Join-Path $PSScriptRoot 'install-android-sdk.ps1')
foreach($repo in $repos){$dir=Join-Path $root $repo; if(Test-Path (Join-Path $dir '.git')){git -C $dir pull --ff-only}else{git clone "https://github.com/amerhwitat/$repo.git" $dir}; Get-ChildItem $dir -Filter settings.gradle.kts -Recurse -File | ForEach-Object { $mobile=$_.Directory.FullName; Push-Location $mobile; try { if(Test-Path '.\gradlew.bat'){cmd /c gradlew.bat clean assembleDebug assembleRelease}else{gradle clean assembleDebug assembleRelease}; if($LASTEXITCODE -ne 0){throw "Gradle failed in $mobile"} } finally {Pop-Location} }}
Write-Host 'Portfolio mobile APK build completed.'
