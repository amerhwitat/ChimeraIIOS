#!/usr/bin/env python3
"""SysV-style service compatibility frontend backed by Kore."""
import os, subprocess, sys
KORE=os.environ.get("CHIMERA_KORECTL","/usr/bin/korectl")
if len(sys.argv)<2:
    print("Usage: service UNIT {start|stop|restart|status}"); raise SystemExit(2)
unit=sys.argv[1]; op=sys.argv[2] if len(sys.argv)>2 else "status"
raise SystemExit(subprocess.call([KORE,op,unit]))
