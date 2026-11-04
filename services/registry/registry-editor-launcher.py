#!/usr/bin/env python3
"""Start the per-user editor service and open its one-use capability URL."""
import os,pathlib,stat,subprocess,sys,time,webbrowser
runtime=pathlib.Path(os.environ.get("XDG_RUNTIME_DIR",f"/run/user/{os.getuid()}"))
token_path=runtime/"chimera-registry-editor.token"
def main():
 subprocess.run(["systemctl","--user","start","chimera-registry-editor.service"],check=True)
 for _ in range(50):
  try:
   st=token_path.stat()
   if st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o600:raise PermissionError("unsafe editor token permissions")
   token=token_path.read_text().strip()
   if len(token)>=32:
    webbrowser.open("http://127.0.0.1:8765/#"+token);return 0
  except FileNotFoundError:time.sleep(.1)
 print("registry editor service did not publish a token",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
