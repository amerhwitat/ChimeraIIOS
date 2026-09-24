#!/usr/bin/env python3
import json,os,subprocess,time
from pathlib import Path
STATE=Path(os.environ.get("CHIMERA_BIOMETRIC_STATE",str(Path.home()/".config/chimera/biometrics.json")))
METHODS={"fingerprint":{"label":"Fingerprint","provider":"fprintd","enabled":True,"enrolled":False,"liveness":False},"face":{"label":"Face recognition","provider":"pam/face","enabled":True,"enrolled":False,"liveness":True},"iris":{"label":"Iris recognition","provider":"pam/iris","enabled":True,"enrolled":False,"liveness":True},"palm":{"label":"Palm recognition","provider":"pam/palm","enabled":True,"enrolled":False,"liveness":True},"hand_geometry":{"label":"Hand geometry","provider":"pam/hand-geometry","enabled":True,"enrolled":False,"liveness":False},"voice":{"label":"Voice recognition","provider":"pam/voice","enabled":False,"enrolled":False,"liveness":True},"vein":{"label":"Palm/finger vein","provider":"pam/vein","enabled":False,"enrolled":False,"liveness":True},"fido2":{"label":"FIDO2 / passkey","provider":"pam-u2f","enabled":True,"enrolled":False,"liveness":False},"smartcard":{"label":"Smart card / PIV","provider":"pam-pkcs11","enabled":True,"enrolled":False,"liveness":False}}
def default(): return {"schema":1,"methods":METHODS,"policy":{"password_fallback":True,"password_required_for_enrollment":True,"remote_biometrics":False,"secure_hardware_preferred":True},"status":"READY","updated":int(time.time())}
def read():
 try:
  d=json.loads(STATE.read_text())
  if d.get("schema")==1:return d
 except Exception:pass
 d=default();write(d);return d
def write(d):
 STATE.parent.mkdir(parents=True,exist_ok=True);t=STATE.with_suffix(".tmp");t.write_text(json.dumps(d,indent=2)+"\n");t.replace(STATE)
def fprint_status():
 try:return subprocess.run(["fprintd-list",os.environ.get("USER","")],capture_output=True,timeout=3).returncode==0
 except Exception:return False
def main():
 d=read()
 if len(os.sys.argv)==1 or os.sys.argv[1] in ("status","get"):
  d["methods"]["fingerprint"]["host_detected"]=fprint_status();d["updated"]=int(time.time());write(d);print(json.dumps(d));return 0
 if len(os.sys.argv)==3 and os.sys.argv[1] in ("enable","disable") and os.sys.argv[2] in d["methods"]:
  d["methods"][os.sys.argv[2]]["enabled"]=os.sys.argv[1]=="enable";d["updated"]=int(time.time());write(d);print(json.dumps(d));return 0
 print("usage: status|get|enable METHOD|disable METHOD");return 2
if __name__=="__main__":raise SystemExit(main())