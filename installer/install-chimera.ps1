param([string]$Edition="",[switch]$Apply)
$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$py=Get-Command python -ErrorAction SilentlyContinue
if(-not $py){ throw "Python 3 is required for the adaptive installer planner." }
$args=@("$root/installer/chimera_installer.py","--output","$root/chimera-install-plan.json")
if($Edition){$args += @("--edition",$Edition)}
if($Apply){$args += @("--apply","--confirm-destructive")}
& $py.Source @args
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Write-Host "Plan written to $root/chimera-install-plan.json"
