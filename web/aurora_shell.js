(()=>{'use strict';
const fallback={categories:[{id:'chimera',title:'Chimera II',apps:[{id:'architecture',title:'Architecture',icon:'A',target:'#architecture'},{id:'isa',title:'ISA Explorer',icon:'◈',target:'#isa-section'},{id:'kernel',title:'Koronos Kernel',icon:'K',target:'#kernel-section'},{id:'system-control-center',title:'System Control Center',icon:'⚙',url:'system_control_center.html'},{id:'terminal',title:'Aurora Terminal',icon:'⌘',target:'#terminal-section'},{id:'desktop-switcher',title:'Desktop Switcher',icon:'▣',url:'desktop_switcher.html'},{id:'retro-emulators',title:'Retro Emulator Center',icon:'🕹',url:'retro_emulators.html'}]}]};
let registry=fallback;
const all=()=>registry.categories.flatMap(c=>c.apps.map(a=>({...a,category:c.title})));
const launch=a=>{if(!a)return;if(a.url){const w=window.open(a.url,'chimera-app-'+a.id,'noopener,noreferrer');if(!w)location.href=a.url;return}const u=new URL(location.href);u.hash='app='+a.id;const w=window.open(u.href,'chimera-'+a.id,'noopener,noreferrer');if(!w)location.href=u.href};
const focus=id=>{const a=all().find(x=>x.id===id);if(a)document.querySelector(a.target||'#main')?.scrollIntoView({behavior:'smooth',block:'center'})};
async function desktopState(){try{const r=await fetch('desktop_profiles.json',{cache:'no-store'});if(!r.ok)return null;return await r.json()}catch{return null}}
async function init(){
 try{const r=await fetch('/aurora_apps.json',{cache:'no-store'});if(r.ok){const x=await r.json();if(x?.categories)registry=x}}catch{}
 const apps=all();
 const dock=document.createElement('aside');dock.className='aurora-launch-dock';
 dock.innerHTML='<b>✦</b><button data-desktop title="Switch desktop">▣</button><button data-control-center title="System Control Center">⚙</button>'+apps.slice(0,8).map(a=>`<button data-app="${a.id}" title="${a.title}">${a.icon}</button>`).join('')+'<button data-menu="1" title="All applications">⋮⋮</button>';
 document.body.append(dock);
 const menu=document.createElement('section');menu.className='aurora-app-center';menu.hidden=true;
 menu.innerHTML='<header><b>All Applications</b><button data-close>×</button></header><input data-search placeholder="Search applications…">'+registry.categories.map(c=>`<div class="app-group"><h3>${c.title}</h3><div class="app-grid">${c.apps.map(a=>`<button data-center="${a.id}"><span>${a.icon}</span><b>${a.title}</b></button>`).join('')}</div></div>`).join('');
 document.body.append(menu);
 dock.addEventListener('click',e=>{const b=e.target.closest('[data-app]');if(b)launch(apps.find(a=>a.id===b.dataset.app));if(e.target.closest('[data-menu]'))menu.hidden=!menu.hidden;if(e.target.closest('[data-desktop]'))window.open('desktop_switcher.html','chimera-desktop-switcher','noopener,noreferrer');if(e.target.closest('[data-control-center]'))window.open('system_control_center.html','chimera-system-control-center','noopener,noreferrer')});
 menu.addEventListener('click',e=>{const b=e.target.closest('[data-center]');if(b){launch(all().find(a=>a.id===b.dataset.center));menu.hidden=true}if(e.target.closest('[data-close]'))menu.hidden=true});
 menu.querySelector('[data-search]').addEventListener('input',e=>{const q=e.target.value.toLowerCase();menu.querySelectorAll('[data-center]').forEach(b=>b.hidden=!b.textContent.toLowerCase().includes(q))});
 const id=new URLSearchParams(location.hash.slice(1)).get('app');if(id)setTimeout(()=>focus(id),120);
 const desktop=await desktopState();
 const apply=profileId=>{if(!desktop)return;const p=desktop.profiles.find(x=>x.id===profileId);if(p){document.body.dataset.desktop=p.id;document.documentElement.dataset.desktop=p.id;document.title='Chimera II — '+p.title}};
 apply(localStorage.getItem('chimera.desktop.profile')||desktop?.default||'aurora-native');
 window.addEventListener('storage',e=>{if(e.key==='chimera.desktop.profile')apply(e.newValue)});
}
init();window.addEventListener('hashchange',()=>focus(new URLSearchParams(location.hash.slice(1)).get('app')));})();
