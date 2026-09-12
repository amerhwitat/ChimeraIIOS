$ErrorActionPreference='Stop'
$root=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$py=Get-Command python -ErrorAction SilentlyContinue
if(-not $py){throw 'Python 3 is required.'}
Write-Host '[BUILD] ChimeraIIOS universal PowerShell runner'
& $py.Source (Join-Path $root 'build-tools/build.py') @args
exit $LASTEXITCODE
