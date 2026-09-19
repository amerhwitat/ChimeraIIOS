#!/bin/sh
set -eu
python3 - <<'PY'
import json,subprocess,platform,datetime
def r(c):
 try:return subprocess.check_output(c,text=True,stderr=subprocess.STDOUT,timeout=30)
 except Exception:return ""
print(json.dumps({"schema":"chimera-hardware-inventory-v1","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat(),"host":{"os":"Darwin","release":platform.release(),"machine":platform.machine()},"devices":[{"class":"system_profiler","raw":r(["system_profiler","SPHardwareDataType","SPPCIDataType","SPUSBDataType","SPDisplaysDataType","SPNetworkDataType"])},{"class":"ioreg","raw":r(["ioreg","-l"])}]},indent=2))
PY
