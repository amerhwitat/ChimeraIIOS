#!/usr/bin/env python3
"""Chimera II OS unified command catalog, Arabic shell front-end and dispatcher."""
import json, os, shutil, subprocess, sys

CATALOG = os.environ.get("CHIMERA_COMMAND_CATALOG", "/usr/share/chimera/commands/chimera-command-list.json")
ARABIC = os.environ.get("CHIMERA_ARABIC_CATALOG", "/usr/share/chimera/commands/chimera-arabic.json")

def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def commands(c):
    out=[]
    for names in c.get("categories", {}).values():
        out.extend(names)
    for key in ("linux_bash","macos_core","windows_cmd_core","powershell_core","vbscript_core","sql_server_core"):
        out.extend(c.get(key, []))
    return sorted(set(out))

def native(c):
    n=c.get("native_chimera", [])
    return n.get("commands", []) if isinstance(n, dict) else n

def amap():
    return load(ARABIC, {"aliases":{}}).get("aliases", {})

def name(x, ar):
    return amap().get(x, x) if ar else x

def main(argv):
    c=load(CATALOG, {})
    cmds=commands(c)
    natives=native(c)
    ar=os.environ.get("CHIMERA_LANG","").lower() in ("ar","arabic","العربية")
    args=argv[1:]
    if len(args)>=2 and args[0] in ("--lang","--language"):
        ar=args[1].lower() in ("ar","arabic","العربية")
        args=args[2:]
    op=args[0] if args else "help"
    if op in ("help","--help","-h"):
        if len(args)>1:
            q=args[1]
            if q in cmds or q in natives:
                print((name(q,ar)+"  ["+q+"]") if ar and name(q,ar)!=q else q)
                print("أمر أصلي/متوافق في فهرس شيميرا II." if ar else "Command registered in the Chimera II OS catalog.")
                return 0
            print("أمر غير معروف: "+q if ar else "Unknown command: "+q, file=sys.stderr)
            return 1
        print("وحدة أوامر نظام شيميرا II" if ar else "Chimera II OS command console")
        print("  chimera commands       عرض أوامر التوافق" if ar else "  chimera commands       List compatibility commands")
        print("  chimera native         عرض أوامر شيميرا الأصلية" if ar else "  chimera native         List native Chimera commands")
        print("  chimera search TERM    البحث في الفهارس" if ar else "  chimera search TERM    Search both catalogs")
        print("  chimera which CMD      تحديد مسار الأمر" if ar else "  chimera which CMD      Resolve command in PATH")
        print("  chimera help CMD       مساعدة الأمر" if ar else "  chimera help CMD       Show command classification")
        print("  chimera exec CMD ...   تنفيذ أمر PATH" if ar else "  chimera exec CMD ...   Execute a PATH command")
        print("  chimera info           معلومات النظام" if ar else "  chimera info           System information")
        print("  chimera doctor         تشخيص البيئة" if ar else "  chimera doctor         Diagnose shell environment")
        return 0
    if op=="commands":
        for x in cmds: print(name(x,ar)+"  ["+x+"]" if ar and name(x,ar)!=x else x)
        return 0
    if op=="native":
        for x in natives: print(name(x,ar)+"  ["+x+"]" if ar and name(x,ar)!=x else x)
        return 0
    if op=="search":
        q=" ".join(args[1:]).lower()
        if not q: return 2
        for x in sorted(set(cmds+natives)):
            if q in x.lower() or q in amap().get(x,"").lower():
                print(name(x,ar)+"  ["+x+"]" if ar and name(x,ar)!=x else x)
        return 0
    if op=="which":
        if len(args)<2: return 2
        p=shutil.which(args[1])
        print(p or ("غير موجود" if ar else "not found"))
        return 0 if p else 1
    if op=="exec":
        if len(args)<2: return 2
        return subprocess.call(args[1:])
    if op=="info":
        print("شيميرا II OS — فهرس أوامر موحّد" if ar else "Chimera II OS — unified command catalog")
        print(("أوامر التوافق: %d | الأوامر الأصلية: %d" if ar else "Compatibility commands: %d | Native commands: %d") % (len(cmds),len(natives)))
        return 0
    if op=="doctor":
        checks=[("catalog",os.path.exists(CATALOG)),("arabic",os.path.exists(ARABIC)),("shell",bool(os.environ.get("SHELL")))]
        for k,ok in checks:
            label={"catalog":"فهرس الأوامر","arabic":"فهرس العربية","shell":"بيئة الصدفة"}.get(k,k) if ar else k
            print(("✓ " if ok else "✗ ")+label)
        return 0 if all(ok for _,ok in checks) else 1
    if op=="shell":
        print("طرفية شيميرا: Bash/POSIX + أسماء عربية إضافية" if ar else "Chimera shell: Bash/POSIX + additive Arabic aliases")
        return 0
    if op in ("version","--version","-V"):
        print("فهرس أوامر شيميرا II 2.1" if ar else "Chimera II OS command catalog 2.1")
        return 0
    print(("عملية شيميرا غير معروفة: " if ar else "Unknown Chimera operation: ")+op, file=sys.stderr)
    return 2

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
