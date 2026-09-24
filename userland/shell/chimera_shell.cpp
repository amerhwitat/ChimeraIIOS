#include "chimera_shell.hpp"
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <string>
#include <vector>
#include <unordered_map>

namespace chimera::shell {

static void out(char* b,std::size_t n,const std::string& s){
    if(n){std::size_t k=s.size()<n-1?s.size():n-1;std::memcpy(b,s.data(),k);b[k]=0;}
}

static int cmd_echo(const CommandContext&,int argc,const char* const* argv,char* o,std::size_t n){
    std::string s;
    for(int i=1;i<argc;i++){if(i>1)s+=' ';s+=argv[i];}
    s+='\n'; out(o,n,s); return 0;
}

static int cmd_pwd(const CommandContext& c,int,char*const*,char*o,std::size_t n){
    out(o,n,std::string(c.cwd?c.cwd:".")+"\n"); return 0;
}

static int cmd_true(const CommandContext&,int,const char*const*,char*,std::size_t){return 0;}
static int cmd_false(const CommandContext&,int,const char*const*,char*,std::size_t){return 1;}

static int cmd_uname(const CommandContext&,int argc,const char*const* argv,char*o,std::size_t n){
    bool a=argc>1&&std::strcmp(argv[1],"-a")==0;
    out(o,n,a?"ChimeraIIOS Koronos POSIX-compatible x86_64\n":"ChimeraIIOS\n");
    return 0;
}

static int invoke(const char* tool,int argc,const char*const* argv,char*o,std::size_t n){
    std::string s=tool;
    for(int i=1;i<argc;i++){
        s+=" \"";
        for(char c:std::string(argv[i])){
            if(c=='\"'||c=='\\')s+='\\';
            s+=c;
        }
        s+="\"";
    }
    s+=" 2>&1";
    FILE*p=::popen(s.c_str(),"r");
    if(!p){out(o,n,std::string(tool)+": unavailable\n");return 127;}
    std::string r; char b[512];
    while(std::fgets(b,sizeof(b),p))r+=b;
    int rc=::pclose(p);
    out(o,n,r);
    return rc==0?0:1;
}

static int cmd_chmctl(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chmctl",argc,argv,o,n);}
static int cmd_settings(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("aurora-settings",argc,argv,o,n);}
static int cmd_diagnostics(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-diagnostics",argc,argv,o,n);}
static int cmd_user_setup(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-user-setup",argc,argv,o,n);}
static int cmd_passwd(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-passwd",argc,argv,o,n);}
static int cmd_groupadd(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-groupadd",argc,argv,o,n);}
static int cmd_perms(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-perms",argc,argv,o,n);}
static int cmd_ad(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-ad",argc,argv,o,n);}
static int cmd_reboot(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-reboot",argc,argv,o,n);}
static int cmd_resource(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-resource-manager",argc,argv,o,n);}
static int cmd_usermod(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-usermod",argc,argv,o,n);}
static int cmd_groupmod(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-groupmod",argc,argv,o,n);}
static int cmd_security_selftest(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-security-selftest",argc,argv,o,n);}
static int cmd_utf8(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-utf8",argc,argv,o,n);}
static int cmd_diskpart(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-diskpart",argc,argv,o,n);}
static int cmd_parted(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-parted",argc,argv,o,n);}
static int cmd_fdisk(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-fdisk",argc,argv,o,n);}
static int cmd_sed(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-sed",argc,argv,o,n);}
static int cmd_awk(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-awk",argc,argv,o,n);}
static int cmd_gdisk(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){return invoke("chm-gdisk",argc,argv,o,n);}
static int cmd_external(const CommandContext&,int argc,const char*const*argv,char*o,std::size_t n){
    if(argc<1)return 127;
    return invoke(argv[0],argc,argv,o,n);
}

static const char* const external_names[]={
    "ls","dir","tree","cp","copy","mv","move","rm","del","erase","rmdir","rd","mkdir","md","touch","ln","readlink","realpath","stat","file","attrib","icacls","chmod","chown","chgrp","find","where","which","command","type","cat","more","less","head","tail","grep","egrep","fgrep","sed","awk","cut","paste","sort","uniq","tr","wc","tee","xargs","diff","cmp","strings","printf","print","env","set","export","unset","printenv","date","cal","time","sleep","timeout","uname","hostname","hostnamectl","lscpu","timedatectl","ver","systeminfo","uptime","free","df","du","lsblk","blkid","mount","umount","format","dd","ps","tasklist","top","htop","kill","taskkill","pkill","pgrep","nice","renice","jobs","fg","bg","wait","nohup","service","systemctl","sc","launchctl","cron","crontab","schtasks","id","who","whoami","users","w","last","login","logout","su","sudo","runas","passwd","useradd","usermod","userdel","groupadd","groupmod","groupdel","groups","net","ip","ifconfig","route","arp","ss","netstat","ping","traceroute","tracepath","pathping","nslookup","dig","host","curl","wget","ftp","tftp","ssh","scp","sftp","rsync","nc","telnet","openssl","gpg","tar","gzip","gunzip","bzip2","bunzip2","xz","unxz","zip","unzip","7z","ar","cpio","make","cmake","ninja","gcc","g++","clang","clang++","ld","as","objdump","readelf","nm","strip","git","svn","python","python3","perl","ruby","java","javac","dotnet","node","npm","cargo","go","rustc","pwsh","powershell","cmd","reg","regedit","robocopy","xcopy","certutil","wevtutil","wmic","dmesg","journalctl","logger","sysctl","systemctl","sw_vers","defaults","open","osascript","xcodebuild","xcrun","codesign","security","plutil","networksetup","diskutil","hdiutil","sips","pbcopy","pbpaste","nano","vi","vim","man","info","apropos","clear","reset","history","help"
};

static const std::unordered_map<std::string,std::string> ar_alias={
    {"مساعدة","chmhelp"},{"مسح","clear"},{"المسار","pwd"},{"اعرض","ls"},{"انتقل","cd"},{"اعرض-ملف","cat"},{"انسخ","cp"},{"انقل","mv"},{"احذف","rm"},{"أنشئ-مجلد","mkdir"},{"أنشئ-ملف","touch"},{"ابحث","grep"},{"ابحث-ملفات","find"},{"العمليات","ps"},{"أوقف-عملية","kill"},{"مراقبة","top"},{"شبكة","ip"},{"اختبر-اتصال","ping"},{"اتصال-آمن","ssh"},{"نسخ-آمن","scp"},{"أرشفة","tar"},{"صلاحيات","chmod"},{"ملكية","chown"},{"اربط","mount"},{"افصل","umount"},{"إعادة-تشغيل","chm-reboot"},{"إيقاف","shutdown"},{"أنشئ-مستخدم","useradd"},{"كلمة-مرور","passwd"},{"أنشئ-مجموعة","groupadd"},{"دليل","man"},{"تحكم-تشيميرا","chmctl"},{"الدليل-النشط","chm-ad"},{"إعداد-المستخدم","chm-user-setup"},{"صلاحيات-الملفات","chm-perms"}
};

static int cmd_help(const CommandContext&,int,char*const*,char*o,std::size_t n){
    out(o,n,
        "Core: cd pwd echo printf env export set unset alias unalias command type which\n"
        "System: chmctl aurora-settings chm-diagnostics chm-reboot chm-resource-manager chm-user-setup chm-passwd chm-groupadd chm-usermod chm-groupmod chm-perms chm-ad chm-security-selftest chm-utf8 chmhelp\n"
        "UTF: chm-utf8 check|count|sanitize|emoji|aliases TEXT; UTF-8 is preserved as bytes, not ASCII.\n"
        "Filesystem: ls cp mv rm mkdir rmdir touch ln find stat file chmod chown du df\n"
        "Text: cat head tail less more grep sed awk cut sort uniq tr wc diff tee xargs\n"
        "Process: ps top htop kill pkill pgrep jobs fg bg wait nice renice nohup\n"
        "Network: ip ss ping traceroute tracepath dig host curl wget ssh scp sftp nc\n"
        "Storage: df du lsblk blkid mount umount dd diskpart parted fdisk gdisk; destructive writes require explicit confirmation.\n"
        "System: uname hostname hostnamectl lscpu timedatectl date uptime free df du lsblk blkid\n");
    return 0;
}

static int cmd_cd(const CommandContext&,int,char*const*,char*o,std::size_t n){
    out(o,n,"cd is a shell-state builtin; use the shell session dispatcher.\n");
    return 0;
}

static const CommandSpec specs[]={
    {"echo",Dialect::Chimera,(CommandHandler)cmd_echo,0},
    {"pwd",Dialect::Chimera,(CommandHandler)cmd_pwd,0},
    {"true",Dialect::Chimera,(CommandHandler)cmd_true,0},
    {"false",Dialect::Chimera,(CommandHandler)cmd_false,0},
    {"uname",Dialect::Chimera,(CommandHandler)cmd_uname,0},
    {"help",Dialect::Chimera,(CommandHandler)cmd_help,0},
    {"chmctl",Dialect::Chimera,(CommandHandler)cmd_chmctl,0},
    {"aurora-settings",Dialect::Chimera,(CommandHandler)cmd_settings,0},
    {"chm-diagnostics",Dialect::Chimera,(CommandHandler)cmd_diagnostics,0},
    {"chm-user-setup",Dialect::Chimera,(CommandHandler)cmd_user_setup,0},
    {"chm-passwd",Dialect::Chimera,(CommandHandler)cmd_passwd,0},
    {"chm-groupadd",Dialect::Chimera,(CommandHandler)cmd_groupadd,0},
    {"chm-usermod",Dialect::Chimera,(CommandHandler)cmd_usermod,0},
    {"chm-groupmod",Dialect::Chimera,(CommandHandler)cmd_groupmod,0},
    {"chm-security-selftest",Dialect::Chimera,(CommandHandler)cmd_security_selftest,0},
    {"chm-perms",Dialect::Chimera,(CommandHandler)cmd_perms,0},
    {"chm-ad",Dialect::Chimera,(CommandHandler)cmd_ad,0},
    {"chm-reboot",Dialect::Chimera,(CommandHandler)cmd_reboot,0},
    {"chm-resource-manager",Dialect::Chimera,(CommandHandler)cmd_resource,0},
    {"chm-utf8",Dialect::Chimera,(CommandHandler)cmd_utf8,0},
    {"diskpart",Dialect::Chimera,(CommandHandler)cmd_diskpart,0},
    {"parted",Dialect::Chimera,(CommandHandler)cmd_parted,0},
    {"fdisk",Dialect::Chimera,(CommandHandler)cmd_fdisk,0},
    {"gdisk",Dialect::Chimera,(CommandHandler)cmd_gdisk,0},
    {"sed",Dialect::Chimera,(CommandHandler)cmd_sed,0},
    {"awk",Dialect::Chimera,(CommandHandler)cmd_awk,0},
    {"cd",Dialect::Chimera,(CommandHandler)cmd_cd,0}
};

const char* dialect_name(Dialect d){
    switch(d){
        case Dialect::POSIX:return "sh";
        case Dialect::Bash:return "bash";
        case Dialect::Zsh:return "zsh";
        case Dialect::Dash:return "dash";
        case Dialect::Ksh:return "ksh";
        case Dialect::Csh:return "csh";
        case Dialect::Tcsh:return "tcsh";
        case Dialect::Fish:return "fish";
        case Dialect::PowerShell:return "powershell";
        case Dialect::Cmd:return "cmd";
        case Dialect::Nushell:return "nushell";
        case Dialect::Elvish:return "elvish";
        case Dialect::Xonsh:return "xonsh";
        case Dialect::Yash:return "yash";
        default:return "chimera";
    }
}

int run_command(const CommandContext& c,const char*name,int argc,const char*const*argv,char*o,std::size_t n){
    std::string resolved=name;
    auto ai=ar_alias.find(resolved);
    if(ai!=ar_alias.end())resolved=ai->second;
    for(const auto&s:specs)
        if(std::strcmp(s.name,resolved.c_str())==0)
            return s.handler(c,argc,argv,o,n);
    for(const char*e:external_names)
        if(resolved==e){
            std::vector<const char*>a(argv,argv+argc);
            if(!a.empty())a[0]=resolved.c_str();
            return cmd_external(c,argc,a.data(),o,n);
        }
    out(o,n,std::string("chimera-shell: command not found: ")+resolved+"\n");
    return 127;
}

static std::vector<std::string> split(const char*line){
    std::vector<std::string>v;
    std::string x;
    bool q=false;
    char qc=0;
    for(const char*p=line;*p;p++){
        if((*p=='\''||*p=='\"')&&(!q||*p==qc)){
            if(q){q=false;qc=0;}else{q=true;qc=*p;}
            continue;
        }
        if(!q&&std::isspace((unsigned char)*p)){
            if(!x.empty()){v.push_back(x);x.clear();}
        }else x+=*p;
    }
    if(!x.empty())v.push_back(x);
    return v;
}

int execute_line(const CommandContext&c,Dialect,const char*line,char*o,std::size_t n){
    auto a=split(line);
    if(a.empty()){if(n)*o=0;return 0;}
    std::vector<const char*>p;
    for(auto&s:a)p.push_back(s.c_str());
    return run_command(c,p[0],(int)p.size(),p.data(),o,n);
}

}
