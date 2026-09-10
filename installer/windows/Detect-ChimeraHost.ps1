$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$arch = $env:PROCESSOR_ARCHITECTURE
[pscustomobject]@{
  Caption = $os.Caption
  Version = $os.Version
  Architecture = $arch
  Is64BitProcess = [Environment]::Is64BitProcess
  DotNetModernEligible = ($os.Version -ge [version]'10.0') -or ($os.Caption -match 'Windows 11') -or ($os.Caption -match 'Windows 10')
} | Format-List
