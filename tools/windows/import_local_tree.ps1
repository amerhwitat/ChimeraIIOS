param(
  [string]$Source = 'C:\tmp\ChimeraIIOS',
  [string]$Destination = (Join-Path $PSScriptRoot '..\..'),
  [switch]$DryRun
)
$ErrorActionPreference='Stop'
$Source=(Resolve-Path $Source).Path
$Destination=(Resolve-Path $Destination).Path
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$backup=Join-Path $Destination ('.chimera-import-backup\'+$stamp)
$skip=@('.git','.chimera-import-backup','build','build-ci','build-local')
Get-ChildItem -LiteralPath $Source -Recurse -File | ForEach-Object {
  $rel=$_.FullName.Substring($Source.Length).TrimStart('\','/')
  if($skip | Where-Object { $rel -eq $_ -or $rel.StartsWith($_+'\') }) { return }
  $target=Join-Path $Destination $rel
  if(Test-Path -LiteralPath $target) {
    $srcHash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    $dstHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if($srcHash -eq $dstHash) { return }
    $b=Join-Path $backup $rel
    if(-not $DryRun){New-Item -ItemType Directory -Force -Path (Split-Path $b) | Out-Null; Copy-Item $target $b -Force}
    Write-Host "BACKUP $rel"
  }
  if(-not $DryRun){New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null; Copy-Item $_.FullName $target -Force}
  Write-Host "IMPORT $rel"
}
if(-not $DryRun){Write-Host "Non-destructive import complete. Existing files were backed up under $backup when changed."}