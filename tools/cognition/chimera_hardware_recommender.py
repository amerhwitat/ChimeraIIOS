#!/usr/bin/env python3
"""Auditable recurrent hardware -> driver recommendation engine."""
import argparse,json,math,os,platform,subprocess,time
from pathlib import Path
FAMILIES={
"gpu":[("Intel",["xe","i915"]),("AMD",["amdgpu","radeon"]),("NVIDIA",["nouveau"]),("Virtual",["virtio_gpu","qxl","vmwgfx"])],
"network":[("Intel",["igc","e1000e","iwlwifi"]),("Realtek",["r8169","rtw88","rtw89"]),("Qualcomm",["ath11k_pci","ath10k_pci"]),("Broadcom",["brcmfmac","tg3"]),("Virtual",["virtio_net"])],
"storage":[("NVMe",["nvme"]),("AHCI/SATA",["ahci","libata"]),("VirtIO",["virtio_blk","virtio_scsi"])],
"audio":[("Intel HDA/SOF",["snd_hda_intel","snd_sof"]),("USB Audio",["snd_usb_audio"])],
"usb":[("xHCI",["xhci_pci"]),("USB storage",["uas","usb_storage"])]}

def recurrent(features):
    s=[0.0]*16
    m=sum(features)/max(1,len(features))
    for _ in range(6): s=[math.tanh(.82*h+.18*m+.005*((i%5)-2)) for i,h in enumerate(s)]
    return sum(s)/len(s)

def modules():
    try:return subprocess.run(["lsmod"],capture_output=True,text=True,timeout=3).stdout.lower()
    except Exception:return ""

def recommend(inv):
    blob=json.dumps(inv,sort_keys=True).lower()+"
"+"\n".join(str(x.get("raw","")) for x in inv.get("devices",[])).lower()
    loaded=modules(); out=[]
    for cls,vendors in FAMILIES.items():
        for vendor,drivers in vendors:
            hits=sum(blob.count(v.lower()) for v in [vendor,*drivers])
            active=sum(loaded.count(d.lower()) for d in drivers)
            if hits or active:
                score=recurrent([min(1,hits/3),min(1,active/2),1 if cls in blob else 0,1 if platform.system()=="Linux" else 0])
                out.append({"class":cls,"vendor_family":vendor,"drivers":drivers,"score":round(score,6),
                            "evidence":{"inventory_hits":hits,"loaded_module_hits":active},
                            "action":"prefer_in_tree_kernel_driver","automatic_install":False})
    out.sort(key=lambda x:(x["class"],-x["score"],x["vendor_family"]))
    return {"schema":"CHIMERA-HARDWARE-RNN-RECOMMENDATIONS-1","generated_at":time.time(),
            "model":{"type":"auditable-recurrent-evidence-scorer","production_hook":"GRU/Transformer optional","training":False},
            "policy":"recommend_only_until_explicit_install_policy","hardware_summary":inv.get("host",{}),"recommendations":out}

ap=argparse.ArgumentParser(); ap.add_argument("--inventory",default=""); ap.add_argument("--output",default="/var/lib/chimera/drivers/ai-recommendations.json"); a=ap.parse_args()
if a.inventory: inv=json.loads(Path(a.inventory).read_text())
else:
    root=Path(__file__).resolve().parents[2]
    inv=json.loads(subprocess.run(["python3",str(root/"hardware/host_scanner.py")],capture_output=True,text=True,check=True).stdout)
result=recommend(inv)
Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
