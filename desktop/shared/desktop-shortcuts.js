(()=>{"use strict";
if(window.ChimeraDesktopShortcuts)return;
const STORE="chimera.desktop.shortcuts.v1";
const allowed=u=>{try{const x=new URL(u,location.href);return ["https:","http:","file:","mailto:"].includes(x.protocol)}catch{return false}};
const read=()=>{try{const x=JSON.parse(localStorage.getItem(STORE)||"[]");return Array.isArray(x)?x.filter(v=>v&&typeof v.name==="string"&&typeof v.target==="string"&&allowed(v.target)):[]}catch{return []}};
const write=x=>localStorage.setItem(STORE,JSON.stringify(x));
const style=document.createElement("style");style.textContent=`
#chm-shortcut-bar{position:fixed;left:14px;bottom:82px;z-index:10020;display:flex;gap:8px;flex-wrap:wrap;max-width:min(60vw,720px);pointer-events:none}
.chm-shortcut{pointer-events:auto;display:grid;place-items:center;gap:3px;min-width:64px;max-width:88px;padding:8px 7px;border:1px solid #9ceaff66;border-radius:13px;background:#071b30c9;color:#effaff;backdrop-filter:blur(16px);box-shadow:0 8px 24px #0007;font:12px system-ui;cursor:pointer;text-align:center}
.chm-shortcut span{font-size:22px}.chm-shortcut small{max-width:76px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#chm-shortcut-tools{position:fixed;right:16px;bottom:16px;z-index:10021;display:flex;gap:6px}
#chm-shortcut-tools button,#chm-shortcut-menu button{border:1px solid #8be8ed66;border-radius:10px;background:#0b2742eF;color:#effaff;padding:9px 12px;font:600 12px system-ui;cursor:pointer;backdrop-filter:blur(16px)}
#chm-shortcut-menu{position:fixed;z-index:10022;display:none;min-width:150px;padding:7px;border:1px solid #8be8ed66;border-radius:12px;background:#071b30f2;box-shadow:0 12px 32px #0009}
#chm-shortcut-menu button{display:block;width:100%;text-align:left;margin:2px 0}
@media(max-width:700px){#chm-shortcut-bar{left:8px;right:8px;bottom:76px;max-width:none}.chm-shortcut{min-width:56px;padding:7px 5px}#chm-shortcut-tools{left:8px;right:8px;bottom:8px;justify-content:flex-end}}
`;document.head.append(style);
const bar=document.createElement("div");bar.id="chm-shortcut-bar";bar.setAttribute("aria-label","Desktop shortcuts");
const tools=document.createElement("div");tools.id="chm-shortcut-tools";
const add=document.createElement("button");add.type="button";add.textContent="+ Add shortcut";add.setAttribute("aria-label","Create an application or document shortcut");
const menu=document.createElement("div");menu.id="chm-shortcut-menu";menu.setAttribute("role","menu");
document.body.append(bar,tools,menu);tools.append(add);
let active=null;
function render(){bar.replaceChildren();read().forEach(item=>{const b=document.createElement("button");b.className="chm-shortcut";b.type="button";b.title=item.name+" — double-click to open; right-click for options";const icon=document.createElement("span");icon.textContent=item.kind==="document"?"📄":item.kind==="web"?"🌐":"▣";const label=document.createElement("small");label.textContent=item.name;b.append(icon,label);b.addEventListener("dblclick",()=>window.open(item.target,"_blank","noopener"));b.addEventListener("click",()=>{b.title="Double-click to open "+item.name});b.addEventListener("contextmenu",e=>{e.preventDefault();active=item;menu.style.left=Math.min(e.clientX,innerWidth-170)+"px";menu.style.top=Math.min(e.clientY,innerHeight-120)+"px";menu.style.display="block"});bar.append(b)})}
function create(){const kind=(prompt("Shortcut type: application, document, or web","application")||"").trim().toLowerCase();if(!["application","document","web"].includes(kind))return;const name=(prompt("Shortcut name","New "+kind)||"").trim();if(!name)return;const target=(prompt(kind==="document"?"Document URL or file:/// path":kind==="web"?"Website URL":"Application URL or desktop entry target","https://")||"").trim();if(!allowed(target)){alert("Only https, http, file and mailto targets are allowed.");return}const items=read();items.push({id:crypto.randomUUID?crypto.randomUUID():String(Date.now()),name,target,kind});write(items);render()}
add.addEventListener("click",create);
const rename=document.createElement("button");rename.textContent="Rename";rename.onclick=()=>{if(!active)return;const name=prompt("New shortcut name",active.name);if(name){const x=read().map(v=>v.id===active.id?{...v,name:name.trim()}:v);write(x);active=null;menu.style.display="none";render()}};
const remove=document.createElement("button");remove.textContent="Remove";remove.onclick=()=>{if(!active)return;write(read().filter(v=>v.id!==active.id));active=null;menu.style.display="none";render()};
const close=document.createElement("button");close.textContent="Close";close.onclick=()=>menu.style.display="none";menu.append(rename,remove,close);document.body.append(menu);
document.addEventListener("click",e=>{if(!menu.contains(e.target))menu.style.display="none"});
window.addEventListener("storage",e=>{if(e.key===STORE)render()});
window.ChimeraDesktopShortcuts={create,render,list:read};render();
})();