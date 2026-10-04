# Chimera II OS native-Windows host-port/device inventory (read-only).
# Enumerates PnP/USB/COM devices without modifying phones.
$ErrorActionPreference = "SilentlyContinue"
$items = Get-PnpDevice | Where-Object { $_.Present -eq $true } |
  Select-Object Class,Status,FriendlyName,InstanceId
[pscustomobject]@{
  schema="CHM-WINDOWS-HOST-PORT-INVENTORY-1"
  timestamp=(Get-Date).ToUniversalTime().ToString("o")
  usb= @($items | Where-Object { $_.Class -match "USB|Android|Bluetooth|Modem|Ports|Portable" })
  all_present_devices=@($items)
  adb=(if (Get-Command adb) { adb devices -l } else { "adb not installed" })
  fastboot=(if (Get-Command fastboot) { fastboot devices -l } else { "fastboot not installed" })
} | ConvertTo-Json -Depth 6
