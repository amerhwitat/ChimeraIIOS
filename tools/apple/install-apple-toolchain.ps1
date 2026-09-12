$ErrorActionPreference = 'Stop'
if (-not $IsMacOS) { throw 'Xcode/iOS SDK installation requires macOS. Use this script from PowerShell 7 on macOS or dispatch a macOS CI runner.' }
if (-not (Get-Command xcodebuild -ErrorAction SilentlyContinue)) { throw 'Install Xcode from Apple before running this bootstrap.' }
if (Get-Command brew -ErrorAction SilentlyContinue) {
  brew install xcodegen ruby bundler
}
if (-not (Get-Command fastlane -ErrorAction SilentlyContinue)) {
  Write-Host 'fastlane not found; install with: gem install fastlane --no-document'
}
xcodebuild -version
xcodegen --version
Write-Host 'Apple toolchain prerequisites are ready.'
