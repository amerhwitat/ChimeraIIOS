[CmdletBinding()]
param(
  [ValidateSet('doctor','deps','configure','build','test','package','install','clean','all')]
  [string]$Command = 'all',
  [Parameter(ValueFromRemainingArguments=$true)] [string[]]$Arguments
)

# Resolve the repository root from this script location; never depend on the caller's working directory.
$CHIMERA_REPO_ROOT = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $CHIMERA_REPO_ROOT
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required.' }
& $python.Source (Join-Path $Root 'tools/build/orchestrator.py') $Command @Arguments
exit $LASTEXITCODE
