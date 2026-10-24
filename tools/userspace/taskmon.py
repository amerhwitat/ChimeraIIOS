#!/usr/bin/env python3
"""TaskMon: portable process and memory KPI viewer for OctavianOS/ChimeraIIOS.

Linux mode reads procfs. Windows mode uses built-in PowerShell/CIM. This is a
hosted/reference userspace utility; native Koronos support requires the OS to
provide a compatible process/memory telemetry API or procfs implementation.
"""
from __future__ import annotations
import argparse, json, os, platform, subprocess, sys, time
from pathlib import Path
from typing import Any

def _read_text(path: Path) -> str:
    try: return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError): return ""

def linux_snapshot(proc_root: Path = Path("/proc")) -> dict[str, Any]:
    mem: dict[str, int] = {}
    for line in _read_text(proc_root / "meminfo").splitlines():
        fields = line.replace(":", "").split()
        if len(fields) >= 2:
            try: mem[fields[0]] = int(fields[1]) * (1024 if len(fields)>2 and fields[2]=="kB" else 1)
            except ValueError: continue
    total = mem.get("MemTotal", 0)
    available = mem.get("MemAvailable", mem.get("MemFree",0)+mem.get("Buffers",0)+mem.get("Cached",0))
    swap_total, swap_free = mem.get("SwapTotal",0), mem.get("SwapFree",0)
    processes = []
    for entry in proc_root.iterdir() if proc_root.exists() else ():
        if not entry.name.isdigit(): continue
        stat = _read_text(entry / "stat")
        left, sep, right = stat.partition("(")
        comm, close, tail = right.rpartition(")")
        fields = tail.strip().split() if close else []
        if not sep or not close or len(fields)<22: continue
        try:
            pid, state = int(left.strip()), fields[0]
            vsize, rss_pages = int(fields[20]), int(fields[21])
            status = _read_text(entry / "status")
            uid = None
            for row in status.splitlines():
                if row.startswith("Uid:"):
                    try: uid = int(row.split()[1])
                    except (ValueError, IndexError): pass
                    break
            processes.append({"pid":pid,"name":comm or "?","state":state,"uid":uid,
              "rss_bytes":max(0,rss_pages)*os.sysconf("SC_PAGE_SIZE"),"virtual_bytes":vsize,
              "cpu_ticks":int(fields[11])+int(fields[12])})
        except (ValueError,OSError,IndexError): continue
    return {"platform":"linux-procfs","memory":{"total_bytes":total,"available_bytes":available,
      "used_bytes":max(0,total-available),"used_percent":round(100*(total-available)/total,2) if total else None,
      "swap_total_bytes":swap_total,"swap_used_bytes":max(0,swap_total-swap_free),
      "swap_used_percent":round(100*(swap_total-swap_free)/swap_total,2) if swap_total else 0.0},
      "processes":processes,"process_count":len(processes),
      "telemetry":{"cpu_percent":None,"note":"CPU percentage requires two samples; RSS/virtual memory are per process."}}

def windows_snapshot() -> dict[str, Any]:
    script = r"""
$os = Get-CimInstance Win32_OperatingSystem
$procs = Get-Process | ForEach-Object {
  [pscustomobject]@{ pid=$_.Id; name=$_.ProcessName; state="?"; rss_bytes=[int64]$_.WorkingSet64; virtual_bytes=[int64]$_.VirtualMemorySize64; cpu_seconds=if ($_.CPU -ne $null) {[double]$_.CPU} else {0.0} }
}
[pscustomobject]@{ total_bytes=[int64]$os.TotalVisibleMemorySize*1024; available_bytes=[int64]$os.FreePhysicalMemory*1024; processes=@($procs) } | ConvertTo-Json -Depth 5 -Compress
"""
    result=subprocess.run(["powershell","-NoProfile","-NonInteractive","-Command",script],check=True,capture_output=True,text=True,timeout=20)
    data=json.loads(result.stdout); total=int(data.get("total_bytes",0)); available=int(data.get("available_bytes",0))
    ps=data.get("processes") or []
    if isinstance(ps,dict): ps=[ps]
    processes=[{"pid":int(p.get("pid",0)),"name":str(p.get("name","?")),"state":str(p.get("state","?")),"uid":None,
      "rss_bytes":int(p.get("rss_bytes",0)),"virtual_bytes":int(p.get("virtual_bytes",0)),
      "cpu_seconds":float(p.get("cpu_seconds",0.0))} for p in ps]
    return {"platform":"windows-powershell","memory":{"total_bytes":total,"available_bytes":available,
      "used_bytes":max(0,total-available),"used_percent":round(100*(total-available)/total,2) if total else None,
      "swap_total_bytes":None,"swap_used_bytes":None,"swap_used_percent":None},"processes":processes,
      "process_count":len(processes),"telemetry":{"cpu_percent":None,"note":"Per-process CPU is cumulative CPU seconds; Windows swap counters are not collected by this adapter."}}

def snapshot() -> dict[str, Any]:
    system=platform.system().lower()
    if system=="linux": return linux_snapshot()
    if system=="windows": return windows_snapshot()
    raise RuntimeError(f"unsupported host platform: {platform.system()}; macOS/BSD and native Koronos adapters are not implemented")

def _fmt_bytes(value: Any) -> str:
    if value is None: return "n/a"
    number=float(value)
    for unit in ("B","KiB","MiB","GiB","TiB"):
        if abs(number)<1024 or unit=="TiB": return f"{number:.1f}{unit}"
        number/=1024
    return f"{number:.1f}TiB"

def render(data: dict[str, Any], sort_by: str, limit: int) -> str:
    processes=list(data["processes"])
    key={"memory":"rss_bytes","virtual":"virtual_bytes","pid":"pid","name":"name"}.get(sort_by,"rss_bytes")
    processes.sort(key=lambda p:p.get(key) or 0,reverse=sort_by!="name")
    m=data["memory"]
    lines=[f"TaskMon — {data['platform']} | processes: {data['process_count']}",
      f"RAM {_fmt_bytes(m['used_bytes'])}/{_fmt_bytes(m['total_bytes'])} ({m['used_percent'] if m['used_percent'] is not None else 'n/a'}%) | available {_fmt_bytes(m['available_bytes'])}",
      f"Swap used {_fmt_bytes(m['swap_used_bytes'])}/{_fmt_bytes(m['swap_total_bytes'])} ({m['swap_used_percent'] if m['swap_used_percent'] is not None else 'n/a'}%)","",
      f"{'PID':>7}  {'STATE':5}  {'RSS':>10}  {'VIRTUAL':>10}  NAME","-"*68]
    for p in processes[:max(0,limit)]:
        lines.append(f"{p.get('pid',0):>7}  {str(p.get('state','?'))[:5]:5}  {_fmt_bytes(p.get('rss_bytes')):>10}  {_fmt_bytes(p.get('virtual_bytes')):>10}  {str(p.get('name','?'))[:40]}")
    lines.extend(["","KPI notes: RSS is resident physical memory; virtual size is address-space size, not physical RAM usage."])
    if data.get("telemetry",{}).get("note"): lines.append(data["telemetry"]["note"])
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Process table and memory/virtual-memory KPI viewer")
    parser.add_argument("--json",action="store_true",help="emit machine-readable JSON")
    parser.add_argument("--sort",choices=("memory","virtual","pid","name"),default="memory")
    parser.add_argument("--limit",type=int,default=30)
    parser.add_argument("--watch",type=float,default=0,metavar="SECONDS",help="refresh repeatedly; Ctrl-C to stop")
    args=parser.parse_args(argv)
    if args.limit<0 or args.watch<0: parser.error("--limit and --watch must be non-negative")
    try:
        while True:
            data=snapshot()
            if args.json: print(json.dumps(data,sort_keys=True))
            else:
                if args.watch: print("\033[2J\033[H",end="")
                print(render(data,args.sort,args.limit))
            if not args.watch: break
            time.sleep(max(0.2,args.watch))
    except KeyboardInterrupt: return 130
    except (OSError,RuntimeError,subprocess.SubprocessError,json.JSONDecodeError) as exc:
        print(f"taskmon: {exc}",file=sys.stderr); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
