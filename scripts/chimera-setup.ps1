
# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments=$true)] [string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required.' }
& $python.Source (Join-Path $Root 'tools/build/orchestrator.py') all @Arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python.Source (Join-Path $Root 'tools/build/orchestrator.py') install @Arguments
exit $LASTEXITCODE
