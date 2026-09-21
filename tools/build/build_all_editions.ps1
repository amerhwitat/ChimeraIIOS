
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
param([string[]]$Edition=@(),[string[]]$Arch=@(),[switch]$Install)
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$py=Get-Command python -ErrorAction SilentlyContinue
if(-not $py){throw 'Python 3 is required.'}
$args=@("$root/tools/build/build_all_editions.py")
foreach($e in $Edition){$args += @('--edition',$e)}
foreach($a in $Arch){$args += @('--arch',$a)}
if($Install){$args += '--install'}
& $py.Source @args
exit $LASTEXITCODE
