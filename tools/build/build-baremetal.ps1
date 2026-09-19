$ErrorActionPreference='Stop'
$Root=(Resolve-Path "$PSScriptRoot\..\..").Path
$Arch=if($env:CHIMERA_ARCH){$env:CHIMERA_ARCH}else{'x86_64'}
$Firmware=if($env:CHIMERA_FIRMWARE){$env:CHIMERA_FIRMWARE}else{'uefi'}
$Build="$Root\build\baremetal-$Arch-$Firmware"
cmake -S $Root -B $Build -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=BAREMETAL -DCHIMERA_ARCH=$Arch -DCHIMERA_FIRMWARE=$Firmware
cmake --build $Build --config Release --parallel
Write-Host "Bare-metal build complete for $Arch/$Firmware. No device is flashed by this script."
