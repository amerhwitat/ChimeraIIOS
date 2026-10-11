#!/usr/bin/env python3
"""Network-first installer preflight for Chimera II OS.

Detects NIC/Wi-Fi devices and driver/firmware evidence, offers safe interactive
configuration, and emits a redacted report. It never stores Wi-Fi passwords.
"""
from __future__ import annotations
import argparse, getpass, json, os, platform, shutil, socket, subprocess, sys, time, uuid
from pathlib import Path

def run(argv, timeout=12, input_text=None):
    try:
        p=subprocess.run(argv, input=input_text, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)

def read(path):
    try: return Path(path).read_text(errors="replace").strip()
    except OSError: return ""

def command(name): return shutil.which(name)

def device_inventory():
    devices=[]
    root=Path("/sys/class/net")
    if root.exists():
        for p in sorted(root.iterdir()):
            if p.name=="lo": continue
            base=p.resolve()
            wireless=(p/"wireless").exists() or (base/"wireless").exists() or (base/"phy80211").exists()
            driver=""
            try: driver=(base/"device/driver").resolve().name
            except OSError: pass
            modalias=read(base/"device/modalias")
            vendor=read(base/"device/vendor"); device_id=read(base/"device/device")
            if not vendor and (base/"device").exists():
                vendor=read(base/"device/idVendor"); device_id=read(base/"device/idProduct")
            carrier=read(p/"carrier")
            devices.append({"name":p.name,"type":"wifi" if wireless else "ethernet_or_other",
                "driver":driver or None,"driver_bound":bool(driver),"modalias":modalias or None,
                "vendor_id":vendor or None,"device_id":device_id or None,
                "operstate":read(p/"operstate") or "unknown","carrier":carrier or "unknown",
                "address":read(p/"address") or None})
    return devices

def driver_evidence(devices):
    modules=set()
    for d in devices:
        if d["driver"]: modules.add(d["driver"])
    loaded=set(read("/proc/modules").splitlines()[i].split()[0] for i in range(len(read("/proc/modules").splitlines())))
    for d in devices:
        d["driver_loaded"]=d["driver"] in loaded if d["driver"] else False
        candidates=[]
        if d["modalias"] and command("modprobe"):
            rc,out,_=run(["modprobe","-R",d["modalias"]],5)
            if rc==0: candidates=sorted(set(x.strip() for x in out.splitlines() if x.strip()))[:16]
        d["candidate_modules"]=candidates
        d["driver_recommendation"]=("keep-current-driver" if d["driver_bound"] else
            "review-candidate-kernel-modules" if candidates else
            "inspect-modalias-and-signed-driver-catalog" if d["modalias"] else "identify-device-before-selecting-driver")
        firmware=[]
        if d["driver"] and command("modinfo"):
            rc,out,_=run(["modinfo","-F","firmware",d["driver"]],5)
            if rc==0: firmware=[x.strip() for x in out.splitlines() if x.strip()][:32]
        d["required_firmware_hints"]=firmware
        d["firmware_hint"]="check-kernel-log-and-linux-firmware-package" if not d["driver_bound"] or firmware else None
    return devices

def addresses():
    rc,out,_=run(["ip","-j","address","show"]) if command("ip") else (127,"","")
    if rc==0:
        try:
            result=[]
            for link in json.loads(out):
                if link.get("ifname")=="lo": continue
                ips=[a.get("local") for a in link.get("addr_info",[]) if a.get("scope")=="global"]
                if ips: result.append({"interface":link.get("ifname"),"addresses":ips})
            return result
        except (ValueError,TypeError): pass
    return []

def connectivity(timeout=3):
    # A direct TCP probe avoids depending on ICMP permission. DNS is checked too.
    dns=False
    try: socket.getaddrinfo("example.com",443); dns=True
    except OSError: pass
    tcp=False
    try:
        with socket.create_connection(("1.1.1.1",443),timeout=timeout): tcp=True
    except OSError: pass
    return {"internet_tcp":tcp,"dns":dns,"internet_ready":tcp and dns}

def scan_wifi():
    if command("nmcli"):
        rc,out,err=run(["nmcli","-t","-f","SSID,SECURITY,SIGNAL","device","wifi","list","--rescan","yes"],20)
        if rc==0:
            items=[]
            for line in out.splitlines():
                parts=line.split(":")
                if parts and parts[0]:
                    items.append({"ssid":parts[0],"security":parts[1] if len(parts)>1 else "",
                                  "signal":parts[2] if len(parts)>2 else ""})
            return items
    if command("iw"):
        rc,out,_=run(["iw","dev"],5)
        if rc==0:
            names=[line.split()[1] for line in out.splitlines() if line.strip().startswith("Interface ")]
            for name in names:
                rc,scan,_=run(["iw","dev",name,"scan"],15)
                if rc==0:
                    ssids=[]
                    for line in scan.splitlines():
                        if line.strip().startswith("SSID:"):
                            ssids.append({"ssid":line.split(":",1)[1].strip(),"security":"inspect access-point capabilities","signal":""})
                    if ssids:return ssids
    return []

def configure_wired(dev):
    name=dev["name"]
    if command("nmcli"):
        return run(["nmcli","--wait","25","device","connect",name],30)
    if command("networkctl"):
        run(["networkctl","renew",name],10)
        time.sleep(2)
        return (0,"networkctl renew requested","") if addresses() else (1,"","No address after networkctl renew")
    if command("dhclient"):
        return run(["dhclient","-v",name],30)
    return 127,"","No supported network manager or DHCP client found"

def configure_wifi(ssid,password,interface=None):
    if not command("nmcli"):
        if not interface or not command("wpa_supplicant") or not command("ip"):
            return 127,"","Wi-Fi setup needs NetworkManager or wpa_supplicant plus iproute2; no credentials were written."
        import tempfile
        def conf_escape(value):
            return value.replace("\\","\\\\").replace('"','\\"').replace("\n","")
        with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",prefix="chimera-wpa-",delete=False) as f:
            os.chmod(f.name,0o600)
            f.write("ctrl_interface=/run/wpa_supplicant\nupdate_config=0\nnetwork={\n")
            f.write('  ssid="'+conf_escape(ssid)+'"\n')
            if password:
                f.write('  key_mgmt=WPA-PSK\n  psk="'+conf_escape(password)+'"\n')
            else:
                f.write("  key_mgmt=NONE\n")
            f.write("}\n")
            path=f.name
        try:
            rc,out,err=run(["ip","link","set","dev",interface,"up"],5)
            if rc==0: rc,out,err=run(["wpa_supplicant","-B","-i",interface,"-c",path],12)
            if rc==0:
                if command("dhclient"): rc,out,err=run(["dhclient","-v",interface],30)
                elif command("udhcpc"): rc,out,err=run(["udhcpc","-i",interface,"-n","-q"],30)
                elif command("networkctl"): rc,out,err=run(["networkctl","renew",interface],15)
                else: return 127,"","Wi-Fi associated, but no DHCP client is installed."
            return rc,out,err
        finally:
            try: os.unlink(path)
            except OSError: pass
    # Password is never placed in argv, shell history, logs, or the installer report.
    if not password:
        # Open Wi-Fi networks need no secret; a secured network fails safely here
        # and the GUI can retry with a password.
        return run(["nmcli","--wait","35","device","wifi","connect",ssid],40)
    # Use a temporary private connection file; password is never in argv or logs.
    import tempfile
    connection_id="Chimera installer Wi-Fi "+uuid.uuid4().hex
    def key_escape(value):
        return value.replace("\\","\\\\").replace("\n","").replace(";","\\;")
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",prefix="chimera-wifi-",delete=False) as f:
        os.chmod(f.name,0o600)
        f.write("[connection]\nid="+connection_id+"\ntype=wifi\nautoconnect=false\n")
        f.write("[wifi]\nmode=infrastructure\nhidden=true\nssid="+key_escape(ssid)+"\n")
        f.write("[wifi-security]\nkey-mgmt=wpa-psk\npsk="+key_escape(password)+"\n")
        f.write("[ipv4]\nmethod=auto\n[ipv6]\nmethod=auto\n")
        path=f.name
    try:
        rc,out,err=run(["nmcli","connection","load",path],10)
        if rc==0: rc,out,err=run(["nmcli","--wait","35","connection","up","id",connection_id],40)
        return rc,out,err
    finally:
        # Keep a successful NetworkManager profile so connectivity survives the
        # transition into installation. Remove only failed temporary profiles.
        if locals().get("rc",1)!=0:
            run(["nmcli","connection","delete","id",connection_id],10)
        try: os.unlink(path)
        except OSError: pass

def recommend(report):
    devices=report["devices"]; ready=report["connectivity"]["internet_ready"]
    rec=[]
    if ready: rec.append({"priority":"info","title":"Internet ready","detail":"Continue to installation-source and package-mirror selection."})
    else:
        wifi=[d for d in devices if d["type"]=="wifi"]
        wired=[d for d in devices if d["type"]!="wifi"]
        if any(d["driver_bound"] for d in wired):
            rec.append({"priority":"high","title":"Try wired DHCP first","detail":"A wired NIC has a bound driver; connect Ethernet and request DHCP."})
        if any(d["driver_bound"] for d in wifi):
            rec.append({"priority":"high","title":"Configure Wi-Fi","detail":"A Wi-Fi interface has a bound driver; scan and connect to an access point."})
        if any(not d["driver_bound"] for d in devices):
            rec.append({"priority":"high","title":"Resolve missing NIC driver/firmware","detail":"Inspect PCI/USB vendor IDs and modalias; choose a signed kernel driver and matching firmware. Do not install an unverified binary."})
        if not devices: rec.append({"priority":"high","title":"No network interface found","detail":"Check UEFI/BIOS device settings, USB tethering/Ethernet adapters, and virtual-machine NIC attachment."})
        if not rec: rec.append({"priority":"medium","title":"Network needs diagnosis","detail":"Check link, DHCP, gateway, DNS, captive portal, and firewall."})
    # The installed RNN/LLM advisor may rank these recommendations. It receives
    # hardware facts only, has a strict timeout, cannot execute actions, and its
    # output is schema-checked. Deterministic rules remain the fallback.
    advisor=command("chimera-rnn-recommend")
    if advisor:
        payload=json.dumps({"task":"installer-network-next-steps","inventory":report,"rules_recommendations":rec})
        rc,out,_=run([advisor,"--task","installer-network-next-steps","--json"],timeout=3,input_text=payload)
        if rc==0:
            try:
                candidate=json.loads(out)
                items=candidate.get("recommendations")
                if isinstance(items,list) and items and all(isinstance(x,dict) and
                    isinstance(x.get("title"),str) and isinstance(x.get("detail"),str) for x in items[:8]):
                    return [{"priority":str(x.get("priority","medium"))[:16],
                             "title":x["title"][:120],"detail":x["detail"][:500],
                             "source":"rnn-llm-advisory"} for x in items[:8]]
            except (ValueError,TypeError,AttributeError):
                pass
    return [dict(x,source="hardware-rules") for x in rec]

def probe():
    devices=driver_evidence(device_inventory())
    return {"schema":"CHIMERA-NETWORK-PREFLIGHT-1","platform":platform.platform(),
            "tools":{x:bool(command(x)) for x in ["ip","nmcli","iw","rfkill","networkctl","dhclient","udhcpc","wpa_supplicant","lspci","lsusb","modprobe","modinfo"]},
            "devices":devices,"addresses":addresses(),"connectivity":connectivity()}

def gui_configure(report):
    """Run a small native Zenity network wizard; secrets stay in Python memory."""
    if not command("zenity"):
        return False
    devices=report.get("devices",[])
    if not devices:
        subprocess.run(["zenity","--warning","--title=Chimera Network Setup",
            "--text=No Ethernet or Wi-Fi interface was detected. Check firmware settings or attach a NIC."],check=False)
        return False
    rows=[]
    for d in devices:
        rows.extend([d["name"],d["type"],d.get("driver") or "driver missing",d.get("operstate","unknown")])
    chosen=subprocess.run(["zenity","--list","--title=Chimera II OS — Step 1: Network",
        "--text=Select an interface to configure. Driver and firmware recommendations are shown in the report.",
        "--column=Interface","--column=Type","--column=Driver","--column=State","--print-column=1",
        "--height=420","--width=850"],input="\n".join("|".join(rows[i:i+4]) for i in range(0,len(rows),4))+"\n",text=True,
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.strip()
    if not chosen:return False
    dev=next((x for x in devices if x["name"]==chosen),None)
    if not dev:return False
    if not dev.get("driver_bound"):
        detail="No driver is bound. Candidate modules: "+(", ".join(dev.get("candidate_modules",[])) or "not found")
        detail+="\nFirmware hints: "+(", ".join(dev.get("required_firmware_hints",[])) or "inspect kernel logs and signed firmware packages")
        subprocess.run(["zenity","--warning","--title=Driver needs attention","--text="+detail],check=False)
        return False
    if dev["type"]=="wifi":
        nets=scan_wifi()
        ssid=""
        if nets:
            choices=[]
            for n in nets: choices.extend([n["ssid"],n.get("security",""),n.get("signal","")])
            ssid=subprocess.run(["zenity","--list","--title=Choose Wi-Fi",
                "--text=Choose a visible network or cancel to enter a hidden SSID.",
                "--column=SSID","--column=Security","--column=Signal","--print-column=1",
                "--height=420","--width=700"],input="\n".join("|".join(choices[i:i+3]) for i in range(0,len(choices),3))+"\n",text=True,
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.strip()
        if not ssid:
            ssid=subprocess.run(["zenity","--entry","--title=Wi-Fi network","--text=Enter Wi-Fi SSID (hidden networks are supported)."],
                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,check=False).stdout.strip()
        if not ssid:return False
        password_result=subprocess.run(["zenity","--password","--title=Wi-Fi credentials"],
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,check=False)
        if password_result.returncode!=0:return False
        password=password_result.stdout.rstrip("\n")
        rc,_,err=configure_wifi(ssid,password,dev["name"])
        if rc:
            subprocess.run(["zenity","--error","--title=Wi-Fi connection failed",
                "--text="+(err or "NetworkManager could not connect. Check password, signal and driver/firmware.")[:700]],check=False)
            return False
    else:
        rc,_,err=configure_wired(dev)
        if rc:
            subprocess.run(["zenity","--error","--title=Ethernet connection failed",
                "--text="+(err or "Could not obtain a network connection. Check cable, link and DHCP.")[:700]],check=False)
            return False
    updated=probe()
    if updated["connectivity"]["internet_ready"]:
        subprocess.run(["zenity","--info","--title=Network ready",
            "--text=Internet connectivity and DNS are available. The installer can now use online mirrors and package repositories."],check=False)
        return True
    subprocess.run(["zenity","--warning","--title=Network partially configured",
        "--text=An interface was configured, but internet/DNS verification failed. You can continue offline or retry from the Network panel."],check=False)
    return False

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe",action="store_true",help="detect hardware and test connectivity")
    ap.add_argument("--report",default="/tmp/chimera-network-preflight.json")
    ap.add_argument("--configure",action="store_true",help="interactively configure Wi-Fi or wired DHCP")
    ap.add_argument("--non-interactive",action="store_true",help="probe only; never prompt or change network")
    ap.add_argument("--gui",action="store_true",help="show the graphical Zenity network-first wizard")
    args=ap.parse_args()
    report=probe()
    if args.gui and not report["connectivity"]["internet_ready"]:
        gui_configure(report)
        report=probe()
    if args.configure and not args.non_interactive and sys.stdin.isatty() and not report["connectivity"]["internet_ready"]:
        print("Chimera II OS — Step 1: Network and Wi-Fi")
        for i,d in enumerate(report["devices"],1):
            print(f"{i}. {d['name']} ({d['type']}); driver={d['driver'] or 'missing'}; state={d['operstate']}")
        options=[d for d in report["devices"] if d["driver_bound"]]
        if options:
            choice=input("Select interface number to configure, or Enter to skip: ").strip()
            if choice.isdigit() and 1<=int(choice)<=len(report["devices"]):
                dev=report["devices"][int(choice)-1]
                if not dev["driver_bound"]:
                    print("No driver is bound. See the driver recommendation; refusing blind driver installation.")
                elif dev["type"]=="wifi":
                    nets=scan_wifi()
                    for i,n in enumerate(nets,1): print(f"{i}. {n['ssid']} [{n['security']}] signal {n['signal']}")
                    ssid=input("Wi-Fi SSID (enter manually if hidden): ").strip()
                    if ssid:
                        password=getpass.getpass("Wi-Fi password (not saved): ")
                        rc,_,err=configure_wifi(ssid,password)
                        if rc: print("Wi-Fi setup failed:",err or "connection manager returned an error")
                else:
                    rc,_,err=configure_wired(dev)
                    if rc: print("Wired setup failed:",err or "network manager returned an error")
        time.sleep(1); report=probe()
    report["recommendations"]=recommend(report)
    # Never include passwords, nmcli connection secrets, or command stderr in report.
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0 if report["connectivity"]["internet_ready"] else (2 if args.configure else 0)
if __name__=="__main__": raise SystemExit(main())
