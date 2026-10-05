param(
    [string]$Root = "C:\tmp\ChimeraIIOS\ROMs",
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$IncludeGenerated
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$catalogDir = Join-Path $RepoRoot "emulation\catalog"
New-Item -ItemType Directory -Force -Path $catalogDir | Out-Null

if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
    throw "ROM root does not exist: $Root"
}

$romExtensions = @{
    ".nes"=@("Nintendo Entertainment System")
    ".fds"=@("Nintendo Famicom Disk System")
    ".sfc"=@("Super Nintendo Entertainment System")
    ".smc"=@("Super Nintendo Entertainment System")
    ".gb"=@("Game Boy")
    ".gbc"=@("Game Boy Color")
    ".gba"=@("Game Boy Advance")
    ".n64"=@("Nintendo 64")
    ".z64"=@("Nintendo 64")
    ".v64"=@("Nintendo 64")
    ".nds"=@("Nintendo DS")
    ".3ds"=@("Nintendo 3DS")
    ".cia"=@("Nintendo 3DS")
    ".iso"=@("Optical disc / ISO")
    ".cue"=@("CD image descriptor")
    ".bin"=@("Raw binary / CD image / firmware")
    ".chd"=@("MAME/CHD disk image")
    ".md"=@("Sega Mega Drive / Genesis")
    ".gen"=@("Sega Mega Drive / Genesis")
    ".sms"=@("Sega Master System")
    ".gg"=@("Sega Game Gear")
    ".pce"=@("PC Engine / TurboGrafx-16")
    ".a26"=@("Atari 2600")
    ".a52"=@("Atari 5200")
    ".a78"=@("Atari 7800")
    ".lnx"=@("Atari Lynx")
    ".ngp"=@("Neo Geo Pocket")
    ".ngc"=@("Neo Geo Pocket Color")
    ".gbx"=@("Game Boy / cartridge image")
    ".rom"=@("Generic ROM / firmware")
    ".elf"=@("Executable / firmware image")
    ".wad"=@("Nintendo Wii/Wii U package")
    ".wbfs"=@("Nintendo Wii")
    ".rvz"=@("Nintendo Wii / GameCube disc image")
    ".gcm"=@("Nintendo GameCube disc image")
    ".dol"=@("Nintendo GameCube executable")
    ".xex"=@("Xbox 360 executable")
}

$emulatorNames = @(
    "retroarch","mednafen","mame","mamedev","pcsx2","dolphin","duckstation",
    "ppsspp","desmume","melonds","mgba","visualboyadvance","snes9x","bsnes",
    "mesen","nestopia","fceux","yuzu","ryujinx","cemu","xemu","xenia",
    "genesis-plus-gx","kronos","flycast","redream","scummvm","dosbox","dosbox-x",
    "qemu","bochs","86box","vice","fs-uae","aethersx2","azahar","lime3ds"
)

function Get-RelativePath([string]$Base, [string]$Path) {
    $baseUri = [System.Uri]((Resolve-Path -LiteralPath $Base).Path.TrimEnd("\") + "\")
    $pathUri = [System.Uri](Resolve-Path -LiteralPath $Path).Path
    return [System.Uri]::UnescapeDataString($baseUri.MakeRelativeUri($pathUri).ToString()).Replace("/","")
}

function Get-DetectedSystems([string]$Extension, [string]$Name) {
    $ext = $Extension.ToLowerInvariant()
    if ($romExtensions.ContainsKey($ext)) { return @($romExtensions[$ext]) }
    return @()
}

function Get-LikelyEmulator([string]$Name, [string]$Extension) {
    $n = $Name.ToLowerInvariant()
    if ($Extension -notin @(".exe",".com",".bat")) { return @() }
    $hits = @()
    foreach ($candidate in $emulatorNames) {
        if ($n -like "*$candidate*") { $hits += $candidate }
    }
    return $hits
}

$items = Get-ChildItem -LiteralPath $Root -File -Recurse -Force |
    Where-Object { $IncludeGenerated -or $_.FullName -notmatch "\emulation\catalog\" }

$roms = New-Object System.Collections.Generic.List[object]
$emulators = New-Object System.Collections.Generic.List[object]
$compatibility = New-Object System.Collections.Generic.List[object]

foreach ($item in $items) {
    $relative = Get-RelativePath $Root $item.FullName
    $sha = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $ext = $item.Extension.ToLowerInvariant()
    $systems = @(Get-DetectedSystems $ext $item.Name)
    $likely = @(Get-LikelyEmulator $item.BaseName $ext)

    $record = [ordered]@{
        path = $relative
        name = $item.Name
        extension = $ext
        size_bytes = [int64]$item.Length
        sha256 = $sha
        modified_utc = $item.LastWriteTimeUtc.ToString("o")
    }

    if ($systems.Count -gt 0) {
        $record["detected_systems"] = $systems
        $record["provenance"] = "local-only"
        $roms.Add([pscustomobject]$record)

        foreach ($system in $systems) {
            $compatibility.Add([pscustomobject]([ordered]@{
                rom_path = $relative
                system = $system
                match_method = "extension"
                emulator_candidates = @()
            }))
        }
    }

    if ($likely.Count -gt 0) {
        $record["likely_emulator_ids"] = $likely
        $record["provenance"] = "local-only"
        $emulators.Add([pscustomobject]$record)
    }
}

$compatibilityBySystem = @{}
foreach ($entry in $compatibility) {
    if (-not $compatibilityBySystem.ContainsKey($entry.system)) {
        $compatibilityBySystem[$entry.system] = New-Object System.Collections.Generic.List[string]
    }
    foreach ($emu in $emulators) {
        foreach ($id in @($emu.likely_emulator_ids)) {
            $compatibilityBySystem[$entry.system].Add($id)
        }
    }
}

foreach ($entry in $compatibility) {
    $entry.emulator_candidates = @($compatibilityBySystem[$entry.system] | Sort-Object -Unique)
}

$metadata = [ordered]@{
    schema_version = "1.0"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    source_root = $Root
    file_count = @($items).Count
}

$romDocument = [ordered]@{ metadata=$metadata; roms=@($roms) }
$emuDocument = [ordered]@{ metadata=$metadata; emulators=@($emulators) }
$compatDocument = [ordered]@{ metadata=$metadata; compatibility=@($compatibility) }

$romDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $catalogDir "roms.local.json") -Encoding UTF8
$emuDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $catalogDir "emulators.local.json") -Encoding UTF8
$compatDocument | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $catalogDir "compatibility.local.json") -Encoding UTF8

Write-Host "[CHIMERA] ROM files: $($roms.Count)"
Write-Host "[CHIMERA] Emulator candidates: $($emulators.Count)"
Write-Host "[CHIMERA] Catalogs written to: $catalogDir"
