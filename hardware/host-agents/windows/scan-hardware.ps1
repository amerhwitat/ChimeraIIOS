# Chimera II OS Windows host hardware agent
$inv=[ordered]@{schema="chimera-hardware-inventory-v1";timestamp=(Get-Date).ToUniversalTime().ToString("o");host=[ordered]@{os="Windows";release=(Get-CimInstance Win32_OperatingSystem).Version;machine=$env:PROCESSOR_ARCHITECTURE};devices=@()}
$inv.devices += [ordered]@{class="pnp";items=@(Get-PnpDevice | Select-Object Status,Class,FriendlyName,InstanceId)}
$inv.host.computer=Get-CimInstance Win32_ComputerSystem
$inv | ConvertTo-Json -Depth 8
