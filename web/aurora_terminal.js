(()=>{'use strict';
const screen=document.querySelector('#screen'),input=document.querySelector('#cmd'),mode=document.querySelector('#shellMode');
if(!screen||!input||!mode)return;
const promptNode=document.querySelector('#prompt');
const home='/home/chimera';let cwd=home,history=[],historyIndex=0;
const env={USER:'chimera',HOME:home,HOSTNAME:'aurora-web',SHELL:'/bin/bash',PWD:cwd};
const dirs=new Set(['/','/home','/home/chimera','/etc','/usr','/usr/bin','/var','/var/log','/mnt','/mnt/drive','/mnt/drive/C']);
const files=new Map([
 ['/etc/os-release','NAME="Chimera II OS (Web Preview)"\nID=chimera\nVERSION=2.8-preview\nKERNEL=Koronos (preview only)\n'],
 [home+'/README.md','Aurora Terminal\nThis is a browser sandbox with an in-memory filesystem. It does not execute host programs or expose host drives.\n'],
 ['/var/log/boot.log','[BOOT] Aurora web preview initialized\n[INFO] Browser shell sandbox ready\n'],
 ['/mnt/drive/C/README.txt','Windows drive bridge preview\nNo real Windows drive is mounted in this browser sandbox.\n']
]);
const builtins=['help','clear','pwd','cd','ls','dir','cat','type','echo','printf','whoami','hostname','uname','env','set','history','man','apropos','whatis','which','command','mkdir','touch','rm','rmdir','tree','date','id','ps','top','free','df','ip','ss','gcc','g++','clang','cmake','ninja','git','python','python3','node','exit'];
const output=(value,kind='')=>{const el=document.createElement('div');el.className=kind;el.textContent=String(value);const line=screen.querySelector('.inputline');screen.insertBefore(el,line);screen.scrollTop=screen.scrollHeight;};
const shellName=()=>mode.value;
const prompt=()=>{const sh=shellName();if(sh==='powershell')return 'PS '+cwd+'>';if(sh==='cmd')return cwd.replaceAll('/','\\')+'>';return 'chimera@aurora:'+cwd+'$';};
const updatePrompt=()=>{promptNode.textContent=prompt();env.PWD=cwd;};
const resolve=p=>{if(!p||p==='~')return home;if(p.startsWith('~/'))p=home+p.slice(1);let parts=(p.startsWith('/')?p:cwd+'/'+p).split('/'),out=[];for(const part of parts){if(!part||part==='.')continue;if(part==='..')out.pop();else out.push(part);}return '/'+out.join('/');};
const split=s=>{const out=[];let token='',quote='';for(let i=0;i<s.length;i++){const ch=s[i];if(quote){if(ch===quote)quote='';else if(ch==='\\'&&i+1<s.length)token+=s[++i];else token+=ch;}else if(ch==='"'||ch==="'")quote=ch;else if(/\s/.test(ch)){if(token){out.push(token);token='';}}else token+=ch;}if(token)out.push(token);return out;};
const list=p=>{const path=resolve(p),names=new Set();for(const d of dirs){if(d!==path&&d.startsWith(path==='/'?'/':path+'/')){const tail=d.slice(path==='/'?1:path.length+1).split('/')[0];if(tail)names.add(tail+'/');}}for(const f of files.keys()){if(f.startsWith(path==='/'?'/':path+'/')){const tail=f.slice(path==='/'?1:path.length+1).split('/')[0];if(tail)names.add(tail);}}return [...names].sort();};
const readManual=async name=>{try{const db=await fetch('man_pages.json').then(r=>r.ok?r.json():{entries:{}});const e=db.entries?.[name];if(!e)return 'No manual entry for '+name;return name+' — '+e.summary+'\nSYNOPSIS: '+e.synopsis;}catch{return 'Manual database is unavailable.';}};
function normalize(command,args){const sh=shellName(),first=command.toLowerCase();if(sh==='powershell'){const m={'get-location':'pwd','set-location':'cd','get-childitem':'ls','get-content':'cat','write-output':'echo','write-host':'echo','clear-host':'clear','get-command':'which','get-process':'ps'};return [m[first]||first,args];}if(sh==='cmd'){const m={dir:'ls',type:'cat',cls:'clear',cd:'cd',ver:'uname'};return [m[first]||first,args];}return [first,args];}
async function execute(raw){
 const parts=split(raw),command=parts.shift()||'',args=parts;
 if(!command)return '';
 const [cmd,a]=normalize(command,args),arg=a[0],path=resolve(arg);
 if(cmd==='help')return 'Shell: '+shellName()+'\nBuilt-ins: '+builtins.join(' ')+'\nUse man COMMAND, apropos KEYWORD, or which COMMAND.\nWeb sandbox: virtual files only; host execution and host-drive access are not available.';
 if(cmd==='clear'){screen.querySelectorAll(':scope > div:not(.inputline)').forEach(x=>x.remove());return '';}
 if(cmd==='pwd')return cwd;
 if(cmd==='cd'){if(!dirs.has(path))return 'cd: no such directory: '+(arg||'');cwd=path;updatePrompt();return '';}
 if(cmd==='ls'){const names=list(arg);return names.length?names.join('  '):'(empty)';}
 if(cmd==='cat'){if(!arg)return 'usage: cat FILE';return files.has(path)?files.get(path):'cat: no such file: '+path;}
 if(cmd==='echo'||cmd==='printf')return a.join(' ');
 if(cmd==='whoami')return env.USER;
 if(cmd==='hostname')return env.HOSTNAME;
 if(cmd==='uname')return 'Chimera II OS Web Preview · Koronos target profile · '+(navigator.platform||'browser host');
 if(cmd==='env'||cmd==='set')return Object.entries(env).map(([k,v])=>k+'='+v).join('\n');
 if(cmd==='history')return history.map((x,i)=>(i+1)+'  '+x).join('\n')||'(empty)';
 if(cmd==='date')return new Date().toString();
 if(cmd==='id')return 'uid=1000(chimera) gid=1000(chimera) groups=1000(chimera)';
 if(cmd==='man')return arg?await readManual(arg):'usage: man COMMAND';
 if(cmd==='whatis')return arg?await readManual(arg):'usage: whatis COMMAND';
 if(cmd==='apropos'){const q=(arg||'').toLowerCase();try{const db=await fetch('man_pages.json').then(r=>r.json());return Object.entries(db.entries||{}).filter(([k,v])=>(k+' '+v.summary).toLowerCase().includes(q)).slice(0,25).map(([k,v])=>k+' — '+v.summary).join('\n')||'No matches';}catch{return 'Manual database unavailable';}}
 if(cmd==='which'||cmd==='command'){const name=cmd==='command'?(a[1]||''):arg;return builtins.includes(name)?'/usr/bin/'+name:name+': not found in the Web sandbox';}
 if(cmd==='mkdir'){if(!arg)return 'usage: mkdir DIRECTORY';if(dirs.has(path)||files.has(path))return 'mkdir: already exists: '+path;dirs.add(path);return '';}
 if(cmd==='touch'){if(!arg)return 'usage: touch FILE';if(!dirs.has(path.slice(0,path.lastIndexOf('/'))||'/'))return 'touch: parent directory does not exist';if(!files.has(path))files.set(path,'');return '';}
 if(cmd==='rm'){if(!arg)return 'usage: rm FILE';if(files.has(path)){files.delete(path);return '';}return 'rm: only files in the virtual filesystem can be removed';}
 if(cmd==='rmdir'){if(!arg)return 'usage: rmdir DIRECTORY';if(path==='/'||path===home)return 'rmdir: protected directory';if(!dirs.has(path))return 'rmdir: no such directory';if(list(path).length)return 'rmdir: directory not empty';dirs.delete(path);return '';}
 if(cmd==='tree'){const root=resolve(arg||'.');return [root,...list(arg||'.').map(x=>'  '+x)].join('\n');}
 if(['ps','top'])return 'PID  TTY  STAT  COMMAND\n1    web  S     aurora-web-preview\n2    web  R     '+shellName()+' (virtual)';
 if(cmd==='free')return '              total        used        free\nMemory:       virtual      n/a         n/a';
 if(cmd==='df')return 'Filesystem      Size  Used  Avail  Use%  Mounted on\nweb-sandbox     n/a   n/a   n/a    n/a   /';
 if(cmd==='ip'||cmd==='ss')return 'Network namespace is not connected in the browser sandbox.';
 if(['gcc','g++','clang','cmake','ninja','git','python','python3','node'].includes(cmd))return cmd+': native execution service is not connected. Use the installed host toolchain or configure a trusted build runner.';
 if(cmd==='exit'){cwd=home;updatePrompt();return 'Closed the virtual '+shellName()+' session (browser remains open).';}
 return command+': command not found. Type help.';
}
input.addEventListener('keydown',async e=>{
 if(e.key==='ArrowUp'){e.preventDefault();historyIndex=Math.max(0,historyIndex-1);input.value=history[historyIndex]||'';return;}
 if(e.key==='ArrowDown'){e.preventDefault();historyIndex=Math.min(history.length,historyIndex+1);input.value=history[historyIndex]||'';return;}
 if(e.key==='Tab'){e.preventDefault();const prefix=input.value.split(/\s+/).pop().toLowerCase();const match=builtins.find(x=>x.startsWith(prefix));if(match)input.value=input.value.slice(0,input.value.length-prefix.length)+match;return;}
 if(e.key!=='Enter')return;
 const raw=input.value.trim();if(!raw)return;
 history.push(raw);historyIndex=history.length;
 output(prompt()+' '+raw,'prompt');
 const result=await execute(raw);if(result)output(result);
 input.value='';updatePrompt();
});
mode.addEventListener('change',()=>{env.SHELL='/bin/'+shellName();updatePrompt();output('Shell profile changed to '+shellName()+'. Commands execute in the browser virtual filesystem only.','muted');});
updatePrompt();output('Interactive shell ready. Type help.','muted');
})();