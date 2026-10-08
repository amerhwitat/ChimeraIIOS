#!/usr/bin/env python3
"""Crawl SS64 indexes and reconcile commands with Chimera II OS.

SS64 is a command-reference/index source only. This tool never copies SS64
prose and never treats SS64 as a binary distributor. Existing target-rootfs
binaries are staged as compatibility providers; missing commands are registered
as native compatibility entries and receive a dispatcher shim.
"""
from __future__ import annotations
import argparse, html.parser, json, os, re, shutil, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
INDEXES={"linux_bash":"https://ss64.com/bash/","macos":"https://ss64.com/mac/","windows_cmd":"https://ss64.com/nt/","powershell":"https://ss64.com/ps/","vbscript":"https://ss64.com/vb/","sql_server":"https://ss64.com/sql/","access":"https://ss64.com/access/","tools":"https://ss64.com/tools/"}
UA="ChimeraIIOS-SS64-Catalog/4.5 (+https://github.com/amerhwitat/ChimeraIIOS)"
class P(html.parser.HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.links=[]; self.a=False; self.h=""; self.t=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a": self.a=True; self.h=dict(attrs).get("href",""); self.t=[]
    def handle_data(self,data):
        if self.a:self.t.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self.a:self.links.append((" ".join("".join(self.t).split()),self.h)); self.a=False

def fetch(url,timeout,retries):
    for n in range(retries+1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"}),timeout=timeout) as r:return r.read().decode("utf-8","replace")
        except (urllib.error.URLError,TimeoutError,OSError):
            if n<retries:time.sleep(.25*(n+1))
    raise RuntimeError(url)

def crawl(seed,platform,max_pages,timeout,retries,delay,max_depth=2):
    p=urllib.parse.urlparse(seed);prefix=p.path.rstrip("/")+"/";q=[(seed,0)];queued={seed};seen=set();out={};failures=0
    deadline=time.monotonic()+max(10.0,float(os.environ.get("CHIMERA_SS64_PLATFORM_BUDGET","90")))
    while q and len(seen)<max_pages and time.monotonic()<deadline:
        u,depth=q.pop(0)
        if u in seen:continue
        x=urllib.parse.urlparse(u)
        if x.netloc!=p.netloc or not x.path.startswith(prefix):continue
        seen.add(u)
        try:html=fetch(u,timeout,retries)
        except Exception as e:failures+=1;print(f"[WARN] {platform}: {e}");continue
        parser=P();parser.feed(html)
        for label,href in parser.links:
            if not href or href.startswith(("#","javascript:","mailto:")):continue
            a=urllib.parse.urljoin(u,href).split("#",1)[0];t=urllib.parse.urlparse(a)
            if t.netloc!=p.netloc or not t.path.startswith(prefix):continue
            if depth<max_depth and a not in seen and a not in queued:q.append((a,depth+1));queued.add(a)
            label=re.sub(r"\s+"," ",label).strip();label=re.sub(r"\s*[•▫]+\s*$","",label).strip()
            if not label or len(label)>160 or len(label)==1 or label in {"Home","Search","Contact","About","Donate","Examples","Syntax","Related","Next","Previous","Back","Top","Index","More"}:continue
            if re.search(r"[A-Za-z0-9_$?&./+:-]",label):out[(label.casefold(),a)]={"name":label,"platform":platform,"source":a}
        if delay:time.sleep(delay)
    return sorted(out.values(),key=lambda x:(x["name"].casefold(),x["source"])),len(seen),failures

def flatten_native(c):
    n=c.get("native_chimera",[])
    if isinstance(n,dict):n=n.get("commands",[])
    return set(n or [])

def rootfs_provider(rootfs,name):
    for p in (rootfs/"usr/bin"/name,rootfs/"bin"/name,rootfs/"usr/sbin"/name,rootfs/"sbin"/name,rootfs/"usr/local/bin"/name):
        if p.is_file() and os.access(p,os.X_OK):return p
    return None

def install_source(repo_root,rootfs,src,dst,mode=0o755):
    s=repo_root/src;d=rootfs/dst
    if not s.exists():return False
    d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d);d.chmod(mode);return True

def reconcile(catalog,rootfs,repo_root):
    cmdlist=repo_root/"system/commands/chimera-command-list.json"
    try:native_doc=json.loads(cmdlist.read_text(encoding="utf-8"))
    except Exception:native_doc={}
    native=flatten_native(native_doc);entries=[]
    for data in catalog["platforms"].values():entries.extend(data.get("commands",[]))
    linux=[x for x in entries if x["platform"]=="linux_bash"]
    compat_root=rootfs/"usr/lib/chimera/compat";compat_bin=compat_root/"bin";compat_bin.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"CHM-COMPAT-1","source":"SS64 command indexes","policy":"Reference names only; providers come from Chimera rootfs or official packages.","commands":{}}
    for x in linux:
        name=x["name"]
        if not re.match(r"^[A-Za-z0-9_.+-]+$",name):continue
        p=rootfs_provider(rootfs,name);item={"name":name,"platform":"linux_bash","source":x["source"],"native_registered":name in native,"provider":"","mode":"registered"}
        if p:
            dst=compat_bin/name
            if not dst.exists():
                try:shutil.copy2(p,dst);dst.chmod(0o755)
                except OSError:pass
            item["provider"]=str(dst);item["mode"]="rootfs-binary"
        else:item["mode"]="compatibility-shim";item["provider"]="chimera-compat (runtime provider lookup)"
        manifest["commands"][name]=item
    for src_name,dst_name in (("tools/runtime/chimera-korectl.py","korectl"),("tools/runtime/chimera-systemctl.py","systemctl"),("tools/runtime/chimera-service.py","service"),("tools/runtime/chimera-compat.py","chimera-compat"),("tools/runtime/kore-manager.py","kore-manager")):
        install_source(repo_root,rootfs,src_name,"usr/bin/"+dst_name)
    install_source(repo_root,rootfs,"tools/runtime/kore-manager.py","usr/libexec/chimera/kore-manager")
    units=repo_root/"system/services/kore-units.json"
    if units.exists():install_source(repo_root,rootfs,"system/services/kore-units.json","etc/chimera/kore-units.json",0o644)
    unit=repo_root/"system/services/kore.service"
    if unit.exists():
        install_source(repo_root,rootfs,"system/services/kore.service","usr/lib/systemd/system/kore.service",0o644)
        w=rootfs/"etc/systemd/system/multi-user.target.wants/kore.service";w.parent.mkdir(parents=True,exist_ok=True)
        try:w.symlink_to("/usr/lib/systemd/system/kore.service")
        except FileExistsError:pass
    policy=repo_root/"system/commands/compatibility-binary-policy.json"
    if policy.exists():install_source(repo_root,rootfs,"system/commands/compatibility-binary-policy.json","usr/share/chimera/commands/compatibility-binary-policy.json",0o644)
    for name in sorted(native | set(manifest["commands"])):
        shim=rootfs/"usr/bin"/name
        if shim.exists():continue
        if re.match(r"^[A-Za-z0-9_.+-]+$",name):
            try:shim.symlink_to("chimera-compat")
            except FileExistsError:pass
    (compat_root/"commands.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    native_doc.setdefault("native_chimera",{})
    if isinstance(native_doc["native_chimera"],dict):
        native_doc["native_chimera"]["commands"]=sorted(native)
        native_doc["native_chimera"]["compatibility_policy"]="Missing SS64-indexed commands are registered as native compatibility entries; runnable binaries are staged only from the Chimera rootfs or official package providers."
        native_doc["native_chimera"]["systemd_compatibility"]=["systemctl","service","korectl","kore.service","systemd target names mapped to Kore targets/services"]
    native_doc["compatibility_commands"] = sorted(set(native_doc.get("compatibility_commands", [])) | set(manifest["commands"]))
    cmdlist.write_text(json.dumps(native_doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

ARABIC_COMMAND_LABELS = {
"ls":"اعرض الملفات","dir":"اعرض الملفات","pwd":"اعرض المسار الحالي","cd":"غيّر المجلد",
"cat":"اعرض محتوى الملف","cp":"انسخ الملفات","mv":"انقل الملفات","rm":"احذف الملفات",
"mkdir":"أنشئ مجلداً","rmdir":"احذف مجلداً","grep":"ابحث داخل النصوص","find":"ابحث عن الملفات",
"chmod":"غيّر الصلاحيات","chown":"غيّر المالك","ps":"اعرض العمليات","kill":"أوقف عملية",
"top":"راقب العمليات","free":"اعرض الذاكرة","df":"اعرض مساحة الأقراص","du":"احسب أحجام الملفات",
"ip":"إعدادات الشبكة","ping":"اختبر الاتصال","curl":"نقل البيانات عبر الشبكة","wget":"تنزيل الملفات",
"ssh":"اتصال آمن عن بُعد","scp":"نسخ آمن للملفات","tar":"أرشفة الملفات","gzip":"ضغط الملفات",
"uname":"معلومات النظام","whoami":"المستخدم الحالي","date":"التاريخ والوقت","echo":"اطبع النص",
"printf":"اطبع نصاً منسقاً","clear":"امسح الشاشة","help":"المساعدة","man":"دليل الأوامر",
"history":"سجل الأوامر","exit":"خروج","get-childitem":"اعرض عناصر المجلد","get-content":"اقرأ محتوى الملف",
"set-location":"غيّر المسار الحالي","get-process":"اعرض العمليات","stop-process":"أوقف عملية",
"get-service":"اعرض الخدمات","get-command":"اعرض الأوامر","get-help":"اعرض المساعدة",
"get-date":"التاريخ والوقت","copy-item":"انسخ العناصر","move-item":"انقل العناصر",
"remove-item":"احذف العناصر","new-item":"أنشئ عنصراً","test-connection":"اختبر الاتصال",
"invoke-webrequest":"أرسل طلب ويب","copy":"انسخ الملفات","del":"احذف الملفات",
"type":"اعرض محتوى الملف","ren":"أعد تسمية الملفات","cls":"امسح الشاشة",
"ipconfig":"إعدادات الشبكة","tasklist":"اعرض العمليات","taskkill":"أنه عملية",
"systeminfo":"معلومات النظام","diskpart":"إدارة الأقراص","chkdsk":"افحص نظام الملفات",
"open":"افتح ملفاً أو تطبيقاً","defaults":"إعدادات macOS","pbcopy":"انسخ إلى الحافظة",
"pbpaste":"اقرأ الحافظة","launchctl":"إدارة خدمات macOS","diskutil":"إدارة الأقراص"
}
def arabic_command_label(name):
    key=name.casefold()
    if key in ARABIC_COMMAND_LABELS:
        return ARABIC_COMMAND_LABELS[key], "translated"
    rules=(
        (("get-","get_"),"استعلم عن"),
        (("set-","set_"),"اضبط"),
        (("new-","new_","create-"),"أنشئ"),
        (("remove-","delete-","del-","clear-","uninstall-"),"أزل أو احذف"),
        (("add-","install-","enable-"),"أضف أو فعّل"),
        (("start-","open-","launch-"),"ابدأ أو افتح"),
        (("stop-","disable-","close-"),"أوقف أو عطّل"),
        (("test-","check-","verify-"),"اختبر أو تحقّق من"),
        (("update-","upgrade-"),"حدّث"),
        (("convert-","format-"),"حوّل أو نسّق"),
        (("export-","save-","write-"),"صدّر أو احفظ"),
        (("import-","load-","read-"),"استورد أو اقرأ"),
        (("copy-","copy_","cp"),"انسخ"),
        (("move-","move_","mv"),"انقل"),
        (("find-","search-","grep"),"ابحث عن"),
        (("list-","show-","display-","dir","ls"),"اعرض"),
        (("remove","delete","erase","rm"),"احذف"),
        (("mount","attach"),"اربط"),
        (("unmount","detach"),"افصل"),
        (("service","daemon"),"خدمة النظام"),
        (("network","net-","ipconfig","ifconfig"),"الشبكة"),
        (("disk","drive","volume"),"الأقراص ووحدات التخزين"),
        (("user","group","account"),"المستخدمون والحسابات"),
    )
    for prefixes,label in rules:
        if key.startswith(prefixes):
            return label+" — "+name, "rule-translated"
    # Translate recognizable English components of compound command names while
    # preserving the exact upstream identifier for safe lookup and execution.
    terms={
        "file":"ملف","files":"الملفات","directory":"مجلد","directories":"المجلدات",
        "folder":"مجلد","folders":"المجلدات","path":"مسار","paths":"المسارات",
        "child":"فرعي","item":"عنصر","items":"العناصر","content":"محتوى",
        "location":"موقع","date":"تاريخ","time":"وقت","event":"حدث","events":"الأحداث",
        "log":"سجل","logs":"السجلات","error":"خطأ","errors":"الأخطاء","warning":"تحذير",
        "config":"إعداد","configuration":"تهيئة","settings":"الإعدادات","feature":"ميزة",
        "package":"حزمة","packages":"الحزم","module":"وحدة","modules":"الوحدات",
        "command":"أمر","commands":"الأوامر","help":"مساعدة","policy":"سياسة",
        "permission":"إذن","permissions":"الأذونات","access":"وصول","control":"تحكم",
        "security":"أمان","certificate":"شهادة","certificates":"الشهادات","key":"مفتاح",
        "credential":"بيانات اعتماد","credentials":"بيانات الاعتماد","group":"مجموعة",
        "groups":"المجموعات","job":"مهمة","jobs":"المهام","task":"مهمة","tasks":"المهام",
        "scheduled":"مجدول","trigger":"مشغّل","variable":"متغير","environment":"بيئة",
        "session":"جلسة","remote":"بعيد","local":"محلي","computer":"حاسوب",
        "server":"خادم","client":"عميل","port":"منفذ","firewall":"جدار ناري","rule":"قاعدة",
        "queue":"طابور","process":"عملية","processes":"العمليات","performance":"أداء",
        "memory":"ذاكرة","cpu":"معالج","service":"خدمة","services":"الخدمات",
        "startup":"بدء التشغيل","shutdown":"إيقاف التشغيل","restart":"إعادة التشغيل",
        "install":"تثبيت","uninstall":"إزالة التثبيت","enable":"تفعيل","disable":"تعطيل",
        "add":"إضافة","remove":"إزالة","new":"جديد","get":"جلب","set":"ضبط","test":"اختبار",
        "check":"فحص","clear":"مسح","start":"بدء","stop":"إيقاف","open":"فتح","close":"إغلاق",
        "copy":"نسخ","move":"نقل","import":"استيراد","export":"تصدير","convert":"تحويل",
        "format":"تنسيق","read":"قراءة","write":"كتابة","find":"بحث","search":"بحث",
        "show":"عرض","display":"عرض","update":"تحديث","upgrade":"ترقية","backup":"نسخ احتياطي",
        "restore":"استعادة","repair":"إصلاح","scan":"فحص","mount":"ربط","unmount":"فصل",
        "attach":"إرفاق","detach":"إلغاء الإرفاق","connect":"اتصال","disconnect":"قطع الاتصال",
        "invoke":"تنفيذ","enter":"دخول","exit":"خروج","push":"دفع","pop":"سحب",
        "send":"إرسال","receive":"استقبال","sync":"مزامنة","compare":"مقارنة",
        "measure":"قياس","resolve":"حل","register":"تسجيل","unregister":"إلغاء التسجيل",
        "network":"شبكة","address":"عنوان","connection":"اتصال","adapter":"مهايئ",
        "disk":"قرص","drive":"محرك","volume":"وحدة تخزين","user":"مستخدم","users":"المستخدمون",
        "account":"حساب","accounts":"الحسابات","system":"النظام","computername":"اسم الحاسوب",
        "printer":"طابعة","print":"طباعة","servicecontroller":"متحكم الخدمات",
        "certificateauthority":"سلطة الشهادات","scheduledtask":"مهمة مجدولة",
        "history":"سجل","result":"نتيجة","results":"النتائج","itemproperty":"خاصية العنصر",
        "childitem":"عنصر فرعي","content":"محتوى","webrequest":"طلب ويب","websession":"جلسة ويب",
        "processmitigation":"تخفيف مخاطر العمليات","eventlog":"سجل الأحداث"
    }
    tokens=re.findall(r"[A-Za-z]+|[0-9]+",re.sub(r"([a-z0-9])([A-Z])",r"\1 \2",name))
    translated=[terms[t.casefold()] for t in tokens if t.casefold() in terms]
    if translated:
        return " ".join(translated)+" ("+name+")", "token-translated"
    return "أمر نظام — "+name, "identifier-preserved"


def attach_arabic_labels(catalog, root):
    merged={}
    for platform_data in catalog.get("platforms",{}).values():
        for row in platform_data.get("commands",[]):
            name=row.get("name","")
            label,status=arabic_command_label(name)
            row["arabic_label"]=label
            row["arabic_status"]=status
            row["arabic_search"]=list(dict.fromkeys([label,name,"أمر "+name]))
            merged.setdefault(name.casefold(),{"name":name,"label":label,"arabic_status":status,"platforms":[]})
            merged[name.casefold()]["platforms"].append(row.get("platform",""))
    desktop={"schema":"CHIMERA-AR-CMD-4","locale":"ar","direction":"rtl","commands":{k:v["label"] for k,v in sorted(merged.items())},"translation_status":{k:v["arabic_status"] for k,v in sorted(merged.items())}}
    system={"schema":"CHIMERA-SS64-AR-2","locale":"ar","commands":{k:{"name":v["name"],"label":v["label"],"translation_status":v["arabic_status"],"platforms":sorted(set(v["platforms"]))} for k,v in sorted(merged.items())}}
    desktop_path=root/"desktop/aurora/arabic_command_catalog.json"
    system_path=root/"system/commands/ss64-command-catalog.ar.json"
    desktop_path.parent.mkdir(parents=True,exist_ok=True)
    system_path.parent.mkdir(parents=True,exist_ok=True)
    desktop_path.write_text(json.dumps(desktop,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    system_path.write_text(json.dumps(system,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Arabic labels generated for {len(merged)} unique command names")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="system/commands/ss64-command-catalog.json");ap.add_argument("--max-pages",type=int,default=80);ap.add_argument("--timeout",type=float,default=10);ap.add_argument("--retries",type=int,default=0);ap.add_argument("--delay",type=float,default=.01);ap.add_argument("--max-depth",type=int,default=2);ap.add_argument("--platforms",nargs="*",choices=sorted(INDEXES));args=ap.parse_args()
    root=Path(__file__).resolve().parents[2];selected=args.platforms or list(INDEXES);out=Path(args.output);catalog={"schema_version":"4.4","product":"Chimera II OS","source":"SS64","source_index":"https://ss64.com/","generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"policy":"Command names, classifications and source URLs only; SS64 prose is not redistributed and SS64 is not treated as a binary distributor.","platforms":{}}
    if out.exists():
        try:
            previous=json.loads(out.read_text(encoding="utf-8")); catalog["platforms"].update(previous.get("platforms",{})); print("[CACHE] Loaded existing command catalog before network crawl")
        except (OSError,json.JSONDecodeError) as exc: print(f"[WARN] Existing catalog ignored: {exc}")
    for platform in selected:
        items,pages,failures=crawl(INDEXES[platform],platform,max(1,args.max_pages),max(1.0,args.timeout),max(0,args.retries),max(0,args.delay),max(0,args.max_depth)); previous=catalog["platforms"].get(platform,{}).get("commands",[]); merged={(x.get("name","").casefold(),x.get("source","")):x for x in previous}; merged.update({(x.get("name","").casefold(),x.get("source","")):x for x in items}); items=sorted(merged.values(),key=lambda x:(x.get("name","").casefold(),x.get("source",""))); catalog["platforms"][platform]={"index":INDEXES[platform],"pages_crawled":pages,"fetch_failures":failures,"command_count":len(items),"commands":items};print(f"{platform}: {len(items)} merged commands across {pages} pages ({failures} failures)")
    attach_arabic_labels(catalog,root);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rootfs=Path(os.environ.get("CHIMERA_ROOTFS_DIR",str(root/"build/iso/rootfs")))
    if rootfs.exists():m=reconcile(catalog,rootfs,root);print(f"Reconciled {len(m['commands'])} Linux/Bash commands; Kore/systemd compatibility staged into {rootfs}")
    return 0
if __name__=="__main__":raise SystemExit(main())
