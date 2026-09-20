# =============================================================================
# CHIMERA II OS - ALL EDITIONS ISO GENERATOR (WSL2 WRAPPER)
# =============================================================================
# PowerShell script to generate all Chimera II OS ISO editions from Windows
#
# Usage: .\generate-all-iso-editions-wsl2.ps1
# =============================================================================

param(
    [string]$WSLDistro = "Ubuntu",
    [string]$OutputPath = "$env:USERPROFILE\Downloads\ChimeraIIOS-ISOs"
)

$ProgressPreference = 'Continue'

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info"    = "Cyan"
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -ForegroundColor Gray -NoNewline
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Test-WSL2 {
    Write-Status "Checking WSL2 installation..." "Info"
    
    try {
        $wslVersion = wsl --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "WSL2 found: $wslVersion" "Success"
            return $true
        }
    }
    catch {
        Write-Status "WSL2 not found" "Error"
        return $false
    }
}

function Test-Docker {
    Write-Status "Checking Docker in WSL2..." "Info"
    
    $dockerVersion = wsl docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker found: $dockerVersion" "Success"
        return $true
    }
    else {
        Write-Status "Docker not available in WSL2" "Error"
        return $false
    }
}

function Test-DiskSpace {
    Write-Status "Checking disk space in WSL2..." "Info"
    
    $dfOutput = wsl df -h / | Select-Object -Last 1
    Write-Status "Disk info: $dfOutput" "Info"
    
    # Extract available space (in KB from df output)
    $diskCheck = wsl bash -c "df / | tail -1 | awk '{print \$4}'"
    $diskKB = [int]$diskCheck
    $diskGB = $diskKB / 1048576
    
    if ($diskGB -lt 50) {
        Write-Status "Insufficient disk space! Need 50GB+, have $diskGB GB" "Error"
        return $false
    }
    
    Write-Status "Disk space OK: $diskGB GB available" "Success"
    return $true
}

function List-DockerImages {
    Write-Status "Listing available Docker images..." "Info"
    
    $images = wsl docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>$null
    
    Write-Host ""
    Write-Host "Docker Images:" -ForegroundColor Cyan
    $images | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
}

function Copy-ScriptToWSL {
    Write-Status "Copying ISO generator script to WSL2..." "Info"
    
    $scriptPath = "C:\tmp\ChimeraIIOS\generate-all-iso-editions.sh"
    $wslPath = "/tmp/generate-all-iso-editions.sh"
    
    if (-not (Test-Path $scriptPath)) {
        Write-Status "Script not found: $scriptPath" "Error"
        return $false
    }
    
    try {
        # Copy using WSL
        wsl bash -c "cat > $wslPath <<'EOF'`n$(Get-Content $scriptPath)`nEOF"
        Write-Status "Script copied to WSL2: $wslPath" "Success"
        return $true
    }
    catch {
        Write-Status "Failed to copy script: $_" "Error"
        return $false
    }
}

function Start-ISOGeneration {
    Write-Status "Starting multi-edition ISO generation..." "Info"
    Write-Status "This will take several hours..." "Warning"
    
    Write-Host ""
    Write-Host "Editions to build:" -ForegroundColor Cyan
    Write-Host "  1. Comprehensive - Full stack (all 13 repos)" -ForegroundColor Green
    Write-Host "  2. Microkernel - Lightweight edition" -ForegroundColor Green
    Write-Host "  3. Mobile - Mobile-optimized" -ForegroundColor Green
    Write-Host "  4. VMware - Virtualization optimized" -ForegroundColor Green
    Write-Host "  5. Standard - Default edition" -ForegroundColor Green
    Write-Host ""
    
    Write-Status "Estimated time: 3-5 hours (depending on system)" "Info"
    Write-Status "Running: sudo bash /tmp/generate-all-iso-editions.sh" "Info"
    Write-Host ""
    
    # Run the ISO generator
    wsl sudo bash /tmp/generate-all-iso-editions.sh
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "ISO generation completed successfully!" "Success"
        return $true
    }
    else {
        Write-Status "ISO generation encountered errors (exit code: $LASTEXITCODE)" "Error"
        return $false
    }
}

function Copy-ISOsToWindows {
    Write-Status "Copying ISO files to Windows..." "Info"
    
    $wslOutputPath = "/root/build-iso-editions/iso-output"
    $windowsPath = "\\wsl$\Ubuntu\root\build-iso-editions\iso-output"
    
    if (-not (Test-Path $windowsPath)) {
        # Try alternate path
        $windowsPath = "\\wsl$\Ubuntu\home\$(wsl whoami)\build-iso-editions\iso-output"
    }
    
    if (-not (Test-Path $windowsPath)) {
        Write-Status "Could not find output path in WSL2" "Error"
        Write-Status "Manual copy required. WSL path: $wslOutputPath" "Warning"
        return $false
    }
    
    # Create output directory
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    
    try {
        Write-Status "Copying from WSL2 to $OutputPath" "Info"
        Copy-Item "$windowsPath\*.iso" -Destination $OutputPath -Force
        Copy-Item "$windowsPath\*.sha256" -Destination $OutputPath -Force
        Copy-Item "$windowsPath\*.md5" -Destination $OutputPath -Force
        Copy-Item "$windowsPath\BUILD_REPORT.txt" -Destination $OutputPath -Force
        
        Write-Status "ISOs copied successfully to $OutputPath" "Success"
        return $true
    }
    catch {
        Write-Status "Failed to copy ISOs: $_" "Error"
        return $false
    }
}

function Show-Results {
    param([bool]$Success)
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    if ($Success) {
        Write-Host "ISO GENERATION COMPLETED SUCCESSFULLY" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        
        if (Test-Path $OutputPath) {
            Write-Host ""
            Write-Host "📁 Output Location: $OutputPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "Files:" -ForegroundColor Cyan
            
            Get-ChildItem "$OutputPath\*.iso" 2>$null | ForEach-Object {
                $size = "{0:N2} GB" -f ($_.Length / 1GB)
                Write-Host "  ✓ $($_.Name) ($size)" -ForegroundColor Green
            }
            
            Write-Host ""
            Write-Host "📋 Next Steps:" -ForegroundColor Cyan
            Write-Host "  1. Verify checksums:" -ForegroundColor Yellow
            Write-Host "     cd $OutputPath" -ForegroundColor Cyan
            Write-Host "     certutil -hashfile *.iso sha256" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  2. Burn to USB:" -ForegroundColor Yellow
            Write-Host "     Download Rufus: https://rufus.ie/" -ForegroundColor Cyan
            Write-Host "     Select ISO and USB drive, click START" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  3. Boot from USB:" -ForegroundColor Yellow
            Write-Host "     Insert USB, restart, press F12/DEL, select USB" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "ISO GENERATION FAILED OR INCOMPLETE" -ForegroundColor Red
        Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  • Check WSL2 disk space: wsl df -h /" -ForegroundColor Cyan
        Write-Host "  • Check Docker: wsl docker images" -ForegroundColor Cyan
        Write-Host "  • View logs: wsl ls -la /root/build-iso-editions/logs/" -ForegroundColor Cyan
        Write-Host "  • Manual run: wsl sudo bash /tmp/generate-all-iso-editions.sh" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
}

function Main {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  CHIMERA II OS - ALL EDITIONS ISO GENERATOR (WSL2)            ║" -ForegroundColor Cyan
    Write-Host "║  Generate ISO files for all Chimera II OS editions            ║" -ForegroundColor Cyan
    Write-Host "║  created by Amer Abdullah Suleiman Hwitat                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    # Pre-flight checks
    Write-Status "═══════════════════ PRE-FLIGHT CHECKS ════════════════════" "Info"
    Write-Host ""
    
    if (-not (Test-WSL2)) {
        Write-Status "Please install WSL2: wsl --install" "Error"
        exit 1
    }
    
    if (-not (Test-Docker)) {
        Write-Status "Docker not available. Install in WSL2: wsl sudo apt install docker.io -y" "Error"
        exit 1
    }
    
    if (-not (Test-DiskSpace)) {
        Write-Status "Please free up at least 50GB of disk space" "Error"
        exit 1
    }
    
    Write-Host ""
    
    List-DockerImages
    
    # Copy script
    if (-not (Copy-ScriptToWSL)) {
        exit 1
    }
    
    # Prompt user
    Write-Host ""
    Write-Host "⚠️  WARNING:" -ForegroundColor Yellow
    Write-Host "  This process will take 3-5 hours" -ForegroundColor Yellow
    Write-Host "  Requires 50GB+ disk space" -ForegroundColor Yellow
    Write-Host "  Will generate 5 bootable ISO images" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "Continue with ISO generation? (yes/no)"
    if ($response -ne "yes") {
        Write-Status "Cancelled by user" "Info"
        exit 0
    }
    
    # Start generation
    Write-Host ""
    Write-Status "═════════════════ STARTING ISO GENERATION ═════════════════" "Info"
    Write-Host ""
    
    $success = Start-ISOGeneration
    
    # Copy results
    if ($success) {
        Write-Host ""
        Write-Status "═════════ COPYING ISO FILES TO WINDOWS ══════════" "Info"
        Copy-ISOsToWindows | Out-Null
    }
    
    # Show results
    Show-Results $success
}

# Run
Main
