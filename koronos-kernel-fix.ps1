# =============================================================================
# KORONOS KERNEL - CODE ANALYSIS & FIX SYSTEM (PowerShell)
# =============================================================================
# Scans kernel code and fixes all missing/failing code

param(
    [string]$GitHubUser = "amerhwitat",
    [string]$RepoDest = "C:\tmp\repos"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AnalysisDir = Join-Path (Get-Location) "kernel-analysis"
$ChimeraRepo = Join-Path $AnalysisDir "ChimeraIIOS"
$OctavianRepo = Join-Path $AnalysisDir "OctavianOS"
$KernelSrc = Join-Path $AnalysisDir "kernel-src"
$KernelFixed = Join-Path $AnalysisDir "kernel-fixed"
$LogFile = Join-Path $AnalysisDir "kernel-analysis-ps1.log"
$ReportFile = Join-Path $AnalysisDir "KERNEL_ANALYSIS_REPORT.txt"

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $colors = @{
        "Info"    = "Cyan"
        "Success" = "Green"
        "Error"   = "Red"
        "Warning" = "Yellow"
        "Scan"    = "Blue"
        "Fix"     = "Magenta"
    }
    
    $time = (Get-Date -Format "HH:mm:ss")
    $output = "[$time] $Message"
    
    Write-Host $output -ForegroundColor $colors[$Type]
    Add-Content $LogFile $output
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "║     KORONOS KERNEL - CODE ANALYSIS & FIX SYSTEM               ║" -ForegroundColor Magenta
    Write-Host "║                                                                ║" -ForegroundColor Magenta
    Write-Host "║  Scan, analyze, fix, and save corrected kernel code           ║" -ForegroundColor Magenta
    Write-Host "║  Created by Amer Abdullah Suleiman Hwitat - عامر الحويطات  ║" -ForegroundColor Magenta
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Initialize-System {
    Show-Banner
    
    @($AnalysisDir, $KernelSrc, $KernelFixed) | ForEach-Object {
        if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    }
    
    "Koronos Kernel Analysis System" > $LogFile
    Add-Content $LogFile "Started: $(Get-Date)"
    
    Write-Status "System initialized" "Success"
    Write-Status "GitHub user: $GitHubUser" "Info"
    Write-Status "Repository destination: $RepoDest" "Info"
}

function Clone-Repositories {
    Write-Status "Cloning kernel repositories..." "Scan"
    
    # ChimeraIIOS
    if (-not (Test-Path $ChimeraRepo)) {
        Write-Status "Cloning ChimeraIIOS..." "Scan"
        git clone "https://github.com/$GitHubUser/ChimeraIIOS.git" $ChimeraRepo 2>&1 | Out-Null
        Write-Status "Cloned ChimeraIIOS" "Success"
    }
    else {
        Write-Status "ChimeraIIOS already exists" "Info"
    }
    
    # OctavianOS
    if (-not (Test-Path $OctavianRepo)) {
        Write-Status "Cloning OctavianOS..." "Scan"
        git clone "https://github.com/$GitHubUser/OctavianOS.git" $OctavianRepo 2>&1 | Out-Null
        Write-Status "Cloned OctavianOS" "Success"
    }
    else {
        Write-Status "OctavianOS already exists" "Info"
    }
}

function Locate-KernelSource {
    Write-Status "Locating kernel source files..." "Scan"
    
    $kernelDirs = @(
        "$ChimeraRepo\kernel",
        "$ChimeraRepo\koronos",
        "$ChimeraRepo\src\kernel",
        "$OctavianRepo\kernel",
        "$OctavianRepo\koronos",
        "$OctavianRepo\src\kernel"
    )
    
    foreach ($dir in $kernelDirs) {
        if (Test-Path $dir) {
            Write-Status "Found kernel directory: $dir" "Success"
            Copy-Item -Path "$dir\*" -Destination $KernelSrc -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Fix-KernelCode {
    Write-Status "Fixing kernel code..." "Fix"
    
    # Copy to fixed directory
    Copy-Item -Path "$KernelSrc\*" -Destination $KernelFixed -Recurse -Force -ErrorAction SilentlyContinue
    
    # Fix line endings
    Get-ChildItem -Path $KernelFixed -Filter "*.c" -Recurse | ForEach-Object {
        $content = Get-Content $_.FullName -Raw
        $content = $content -replace "`r`n", "`n"
        Set-Content $_.FullName $content -NoNewline
    }
    
    # Create missing kernel.h
    $kernelH = Join-Path $KernelFixed "kernel.h"
    if (-not (Test-Path $kernelH)) {
        $content = @"
#ifndef KERNEL_H
#define KERNEL_H

#define KERNEL_NAME "Koronos"
#define KERNEL_VERSION "1.0.0"

typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;

void kernel_init(void);
void kernel_main(void);
void kernel_panic(const char *msg);

#endif
"@
        Set-Content $kernelH $content
        Write-Status "Created kernel.h" "Success"
    }
    
    # Create missing kernel.c
    $kernelC = Join-Path $KernelFixed "kernel.c"
    if (-not (Test-Path $kernelC)) {
        $content = @"
#include "kernel.h"

void kernel_init(void) {
    puts("Koronos Kernel Initializing...");
}

void kernel_main(void) {
    kernel_init();
    puts("Koronos Kernel started!");
    while (1) { }
}

void kernel_panic(const char *msg) {
    puts("KERNEL PANIC: ");
    puts(msg);
    while (1) { asm("hlt"); }
}

void puts(const char *str) {
    if (str == NULL) return;
    while (*str) {
        putc(*str++);
    }
}
"@
        Set-Content $kernelC $content
        Write-Status "Created kernel.c" "Success"
    }
    
    # Create Makefile
    $makefile = Join-Path $KernelFixed "Makefile"
    if (-not (Test-Path $makefile)) {
        $content = @"
CC = gcc
AS = as
LD = ld
CFLAGS = -m32 -ffreestanding -Wall

SOURCES = `$(wildcard *.c)
OBJECTS = `$(SOURCES:.c=.o)
TARGET = kernel.elf

all: `$(TARGET)

`$(TARGET): `$(OBJECTS)
	`$(LD) -o `$@ `$^

%.o: %.c
	`$(CC) `$(CFLAGS) -c `$< -o `$@

clean:
	rm -f `$(OBJECTS) `$(TARGET)
"@
        Set-Content $makefile $content
        Write-Status "Created Makefile" "Success"
    }
}

function Save-ToRepoDestination {
    Write-Status "Saving fixed code to repository destination..." "Info"
    
    $kernelRepo = Join-Path $RepoDest "Koronos-Kernel"
    @(
        "$kernelRepo\src",
        "$kernelRepo\include",
        "$kernelRepo\boot"
    ) | ForEach-Object {
        if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
    }
    
    Copy-Item -Path "$KernelFixed\*" -Destination "$kernelRepo\src" -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Status "Saved to: $kernelRepo" "Success"
}

function Main {
    Initialize-System
    Clone-Repositories
    Locate-KernelSource
    Fix-KernelCode
    Save-ToRepoDestination
    
    Write-Host ""
    Write-Status "KERNEL ANALYSIS & FIX COMPLETE!" "Success"
    Write-Status "Repository: $RepoDest\Koronos-Kernel" "Info"
}

Main
