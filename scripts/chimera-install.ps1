[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments=$true)] [string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 is required.' }
& $python.Source (Join-Path $Root 'tools/build/orchestrator.py') install @Arguments
exit $LASTEXITCODE
