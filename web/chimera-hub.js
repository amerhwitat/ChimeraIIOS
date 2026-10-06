(() => {
'use strict';
const ART='desktop/aurora/assets/library/Aurora-Wayland-Glass-Desktop.png(1).jpg';
const BRIDGE='http://127.0.0.1:8765';
const systems=[
['pacman','Pac-Man','Arcade','Namco'],['galaga','Galaga','Arcade','Namco'],['galaxian','Galaxian','Arcade','Namco'],['dkong','Donkey Kong','Arcade','Nintendo'],['mspacman','Ms. Pac-Man','Arcade','Midway'],['sf2','Street Fighter II','Arcade','Capcom'],['1942','1942','Arcade','Capcom'],['outrun','Out Run','Arcade','Sega'],['neogeo','Neo Geo','Arcade','SNK'],['c64','Commodore 64','Computer','Commodore'],['apple2','Apple II','Computer','Apple'],['a2600','Atari 2600','Console','Atari'],['a5200','Atari 5200','Console','Atari'],['a7800','Atari 7800','Console','Atari'],['nes','NES/Famicom','Console','Nintendo'],['snes','SNES','Console','Nintendo'],['sms','Master System','Console','Sega'],['genesis','Mega Drive/Genesis','Console','Sega'],['msx','MSX/MSX2','Computer','Microsoft'],['spectrum','ZX Spectrum','Computer','Sinclair'],['amiga','Amiga','Computer','Commodore'],['arcade','Arcade machines','Arcade','MAME']];
const gameCatalog=[
['supertuxkart','SuperTuxKart','3D Racing','Open-source','native-elf'],['luanti','Luanti','3D Voxel','Open-source','native-elf'],['xonotic','Xonotic','3D Arena FPS','BizX Game Vault','native-elf'],['red-eclipse','Red Eclipse','3D Arena FPS','BizX Game Vault','native-elf'],['veloren','Veloren','3D RPG','BizX Game Vault','native-elf'],['unvanquished','Unvanquished','3D Strategy/FPS','BizX Game Vault','native-elf'],['dark-mod','The Dark Mod','3D Stealth','BizX Game Vault','native-elf'],['flightgear','FlightGear','Flight Simulator','BizX Game Vault','native-elf'],['stunt-rally','Stunt Rally','3D Rally','Free 3D Games','native-elf'],['lugaru','Lugaru','3D Action','Free 3D Games','native-elf'],['0ad','0 A.D.','RTS','BizX Game Vault','native-elf'],['openmw','OpenMW','RPG Engine','BizX Game Vault','native-elf'],['trex','T-Rex Runner','Runner','BizXtreme','browser'],['holdem','Texas Hold’em','Card Game','BizXtreme','browser'],['blackjack','Blackjack','Card Game','BizXtreme','browser'],['solitaire','Klondike Solitaire','Card Game','BizXtreme','browser'],['freecell','FreeCell','Card Game','BizXtreme','browser'],['hearts','Hearts','Card Game','BizXtreme','browser'],['spades','Spades','Card Game','BizXtreme','browser'],['crazy-eights','Crazy Eights','Card Game','BizXtreme','browser'],['war','War','Card Game','BizXtreme','browser'],['chimera-frontier','Chimera Frontier','Original','BizX Originals','planned'],['chimera-arena','Chimera Arena','Original','BizX Originals','planned'],['chimera-rpg','Chimera RPG','Original','BizX Originals','planned'],['chimera-tactical','Chimera Tactical','Original','BizX Originals','planned'],['chimera-world','Chimera World','Original','BizX Originals','planned']
];
const bizxModules=[
['Game platform','Deterministic state, story/scene graph, branching quests, dialogue conditions, inventory, factions, combat, abilities, economy, NPC schedules, vehicles, world events, procedural streaming, save/load and replay.'],
['Commerce','Catalog → quote → wallet connection → payment preview → explicit provider signing → broadcast → independent confirmation → entitlement/fulfillment.'],
['Wallet boundary','Public balances, transaction verification and explorer references. Private keys and recovery phrases never enter the Web UI database or game telemetry.'],
['NetworkUnified','Authoritative sessions, lobbies, presence, WebSocket/WebRTC adapters, prediction/rollback contracts and platform-neutral network boundaries.'],
['Asset provenance','Source URL, license, attribution, checksum and import date for external assets; proprietary content is never silently mirrored.'],
['Multi-runtime','Node.js, Java, Python, Unity C#, Unreal C++, mobile and browser adapters share data contracts without mixing implementations.'],
['BizX Game Vault','Open-source game catalog, build/license manifests, SHA-256 package policy and hardware capability classification.'],
['Security','Deterministic simulation is authoritative; AI/UI cannot invent HP, currency, inventory, quest completion or network authority.']
];
const bx={
kpis:[['Score','0'],['XP','0'],['Expedition','0%'],['Play time','0m'],['Peers','0'],['Rank','—']],
chapters:[['Awakening','Restore the base beacon · Complete first expedition · Claim starter supply'],['The Broken Signal','Decode signal fragments · Recover navigation core · Open northern route'],['Frontier Alliance','Earn faction trust · Defend a relay · Choose an alliance'],['The Black Aurora','Locate an Aurora shard · Survive night expedition · Unlock collection'],['The Great Expedition','Collect components · Contribute globally · Enter final expedition']],
events:[['Frontier Weekend','Weekly · bonus progression and free daily claims'],['Aurora Night','Seasonal · exploration rewards and cosmetics'],['Faction Wars','Monthly · faction objectives and map-control rewards'],['Lost Signal Hunt','Rotating · clues, caches and lore'],['Great Expedition','Seasonal · cooperative world objective']],
inventory:[['Frontier Outfit','Cosmetic ×1'],['Explorer Tool','Equipment ×1'],['Rookie Runner Skin','Cosmetic ×1'],['Frontier Map','Content ×1'],['Starter Supply Crate','Consumable ×3'],['Inventory Expansion','Utility ×5']],
market:[['30-Day Access','Time'],['7-Day XP Boost','Boost'],['10 Inventory Slots','Utility'],['Aurora Skin','Cosmetic'],['Explorer Map Pack','Content'],['Expedition Kit','Equipment'],['Frontier Resource Cache','Consumable'],['Hardware Wallet Case','Accessory']]
};
const controls={
up:'ArrowUp',down:'ArrowDown',left:'ArrowLeft',right:'ArrowRight',fire1:'KeyZ',fire2:'KeyX',start:'Enter',select:'ShiftLeft',menu:'Tab',pause:'Escape',virtualKeyboard:'F12',save:'F5',load:'F7'
};
let db,selectedMachine=null,listenAction=null;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function log(s){const el=$('#dbLog');if(el){el.textContent+=(el.textContent?'\n':'')+s;el.scrollTop=el.scrollHeight}}
function metrics(el,rows){$(el).innerHTML=rows.map(x=>'<div class="metric"><span>'+esc(x[0])+'</span><strong>'+esc(x[1])+'</strong></div>').join('')}
function rows(el,arr){$(el).innerHTML=arr.map(x=>'<div class="list-row"><strong>'+esc(x[0])+'</strong><span class="muted">'+esc(x[1])+'</span></div>').join('')}
function openDB(){
 return new Promise((resolve,reject)=>{const r=indexedDB.open('chimera-ii-control',3);r.onupgradeneeded=()=>{const d=r.result;['settings','machines','games','controls','saves'].forEach(n=>{if(!d.objectStoreNames.contains(n))d.createObjectStore(n,{keyPath:'id'})})};r.onsuccess=()=>{db=r.result;resolve(db)};r.onerror=()=>reject(r.error)})
}
function put(store,obj){return new Promise((res,rej)=>{const t=db.transaction(store,'readwrite');t.objectStore(store).put(obj);t.oncomplete=()=>res();t.onerror=()=>rej(t.error)})}
function all(store){return new Promise((res,rej)=>{const t=db.transaction(store);const r=t.objectStore(store).getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
function initDBData(){
 return Promise.all([all('machines'),all('games')]).then(([m,g])=>Promise.all([
  m.length?null:Promise.all(systems.map(s=>put('machines',{id:s[0],name:s[1],family:s[2],manufacturer:s[3],favorite:false}))),
  g.length?null:Promise.all(gameCatalog.map(x=>put('games',{id:x[0],title:x[1],genre:x[2],provider:x[3],layer:x[4],favorite:false})))
 ]))
}
async function bridge(path,body){
 try{const r=await fetch(BRIDGE+path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});if(!r.ok)throw Error(r.status);return await r.json()}catch(e){throw e}
}
async function checkBridge(){
 try{const r=await bridge('/health');$('#bridgeDot').className='dot ok';$('#bridgeText').textContent='Local bridge: '+(r.version||'online');$('#amigaStatus').textContent='Bridge online. Local cores are available to launch outside Pages.';return true}
 catch(e){$('#bridgeDot').className='dot bad';$('#bridgeText').textContent='Local bridge: offline';$('#amigaStatus').textContent='Bridge offline. Install/start tools/amiga-local-core/bridge.py locally to launch the Amiga core.';return false}
}
function show(view){$$('.view').forEach(v=>v.classList.toggle('active',v.id==='view-'+view));$$('.hub-nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===view));location.hash=view}
function setupNav(){$$('.hub-nav button').forEach(b=>b.onclick=()=>show(b.dataset.view));const h=location.hash.slice(1);if(h&&$('#view-'+h))show(h)}
function overview(){metrics('#overviewMetrics',[['Systems',systems.length],['Games',gameCatalog.length],['BizX modules',bizxModules.length],['BizXtreme events',bx.events.length],['Input actions',Object.keys(controls).length],['DB schema','v3']])}
function renderMame(){
 const q=($('#mameSearch').value||'').toLowerCase(), f=$('#mameFilter').value;
 const list=systems.filter(s=>(f==='all'||(f==='favorite'&&false)||s[2].toLowerCase()===f||s[2].toLowerCase().includes(f))&&(s.join(' ').toLowerCase().includes(q)));
 $('#mameCount').textContent=list.length+' machines';
 $('#machineList').innerHTML=list.map(s=>'<div class="machine '+(selectedMachine?.[0]===s[0]?'selected':'')+'" data-id="'+esc(s[0])+'"><strong>'+esc(s[1])+'</strong><small>'+esc(s[2])+' · '+esc(s[3])+' · '+esc(s[0])+'</small></div>').join('');
 $$('.machine').forEach(x=>x.onclick=()=>{selectedMachine=systems.find(s=>s[0]===x.dataset.id);renderMame();renderMachineDetail()})
}
function renderMachineDetail(){if(!selectedMachine){$('#machineDetail').innerHTML='<div class="empty">Select a machine.</div>';return}const s=selectedMachine;$('#machineDetail').innerHTML='<div class="section-head"><div><span class="eyebrow">'+esc(s[2])+'</span><h3>'+esc(s[1])+'</h3><p class="muted">MAME driver: '+esc(s[0])+' · '+esc(s[3])+'</p></div><button id="favMachine">☆ Favorite</button></div><div class="chips"><span>ROM verify</span><span>Software lists</span><span>Slots</span><span>Input remapping</span><span>Save states</span><span>Debugger</span><span>Snapshots</span><span>Recording</span></div>';$('#favMachine').onclick=()=>{put('machines',{id:s[0],name:s[1],family:s[2],manufacturer:s[3],favorite:true});log('Favorite: '+s[1])}}
function mameCommand(extra=[]){if(!selectedMachine)return 'mame';const path=$('#mameRomPath').value.trim()||'roms';let c=['mame',selectedMachine[0],'-rompath',path,'-video',$('#mameVideo').value];if($('#mameWindow').value==='fullscreen')c.push('-maximize');const sp=Number($('#mameSpeed').value||1);if(sp!==1)c.push('-speed',sp);if($('#autosave').value==='on')c.push('-autosave');if($('#rewind').value==='on')c.push('-rewind','-rewind_capacity',$('#rewindCap').value);if($('#debugger').value)c.push(...extra);return c.join(' ')}
function updateMameCommand(){if($('#mameCommand'))$('#mameCommand').textContent=mameCommand()}
function setupMame(){
 $('#mameSearch').oninput=renderMame;$('#mameFilter').onchange=renderMame;
 $$('#view-mame input,#view-mame select').forEach(x=>x.addEventListener('change',updateMameCommand));
 $$('.tab').forEach(b=>b.onclick=()=>{$$('.tab').forEach(x=>x.classList.remove('active'));$$('.mtab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelector('[data-mtab-panel="'+b.dataset.mtab+'"]').classList.add('active')});
 $('#mameLaunch').onclick=async()=>{const ok=await checkBridge();if(!ok){alert('Local bridge is offline.');return}try{await bridge('/launch/mame',{command:mameCommand()});log('MAME launch requested: '+mameCommand())}catch(e){alert('Bridge rejected MAME launch: '+e.message)}};
 $('#mameCopy').onclick=()=>navigator.clipboard?.writeText(mameCommand()).then(()=>log('MAME command copied.'));
 $('#mameValidate').onclick=async()=>{try{const r=await bridge('/mame/validate',{machine:selectedMachine?.[0],rompath:$('#mameRomPath').value||'roms'});log(JSON.stringify(r))}catch(e){log('Validation requires local bridge.')}};
 $('#mameImport').onclick=()=>{const i=document.createElement('input');i.type='file';i.accept='.xml';i.onchange=async()=>{const f=i.files[0];if(!f)return;const t=await f.text();const doc=new DOMParser().parseFromString(t,'application/xml');const nodes=[...doc.querySelectorAll('machine')];for(const n of nodes.slice(0,5000)){const id=n.getAttribute('name');if(!id)continue;await put('machines',{id,name:n.getAttribute('description')||id,family:'MAME',manufacturer:n.querySelector('manufacturer')?.textContent||'',favorite:false})}log('Imported '+nodes.length+' MAME machines from listxml.');const ms=await all('machines');$('#mameCount').textContent=ms.length+' database entries';renderMame()};i.click()};
 $('#mameInputPanel').innerHTML='<div class="control-grid">'+Object.entries(controls).map(([k,v])=>'<div><strong>'+esc(k)+'</strong><br><span class="muted">'+esc(v)+'</span></div>').join('')+'</div>';
 $('#stateSave').onclick=()=>log('State-save request queued for slot '+$('#stateSlot').value);$('#stateLoad').onclick=()=>log('State-load request queued for slot '+$('#stateSlot').value);$('#record').onclick=()=>log('Input recording request queued.');$('#snapshot').onclick=()=>log('Snapshot request queued.');$('#debugLaunch').onclick=()=>log('Debugger launch: '+mameCommand(['-debug','-debugger',$('#debugger').value]));$('#mediaMount').onclick=()=>log('Media mount request: '+$('#mediaSlot').value+' <- '+$('#mediaPath').value);$('#mediaEject').onclick=()=>log('Media eject request: '+$('#mediaSlot').value);
 renderMame();renderMachineDetail();updateMameCommand()
}
function renderGames(){
 const q=($('#gameSearch').value||'').toLowerCase(), fam=$('#gameFamily').value;
 const rows=gameCatalog.filter(x=>(fam==='all'||x[2]===fam)&&(x.join(' ').toLowerCase().includes(q)));
 $('#gamesGrid').innerHTML=rows.map(x=>'<article class="game-card"><h3>'+esc(x[1])+'</h3><p>'+esc(x[2])+' · '+esc(x[3])+'</p><div class="chips"><span>'+esc(x[4])+'</span><span>cataloged</span></div><div class="actions"><button data-game="'+esc(x[0])+'">Add favorite</button></div></article>').join('');
 $$('#gamesGrid button').forEach(b=>b.onclick=()=>{const x=gameCatalog.find(g=>g[0]===b.dataset.game);put('games',{id:x[0],title:x[1],genre:x[2],provider:x[3],layer:x[4],favorite:true});b.textContent='Favorited';log('Game favorite: '+x[1])});
 $('#gameStats').innerHTML='<span>'+rows.length+' results</span><span>'+new Set(gameCatalog.map(x=>x[2])).size+' genres</span><span>Legal/open-source catalog policy</span>';
}
function setupGames(){const fam=[...new Set(gameCatalog.map(x=>x[2]))].sort();$('#gameFamily').innerHTML='<option value="all">All genres</option>'+fam.map(x=>'<option>'+esc(x)+'</option>').join('');$('#gameSearch').oninput=renderGames;$('#gameFamily').onchange=renderGames;renderGames()}
function renderBizx(){metrics('#bizxKpis',[['Systems contract','deterministic'],['Languages','Node · Java · Python'],['Game systems','20+'],['Wallet boundary','provider'],['Network','authoritative'],['Asset policy','verified']]);$('#bizxModules').innerHTML=bizxModules.map(x=>'<article class="panel"><h3>'+esc(x[0])+'</h3><p class="muted">'+esc(x[1])+'</p></article>').join('')}
function renderBizXtreme(){metrics('#bxKpis',bx.kpis);rows('#chapters',bx.chapters);rows('#events',bx.events);rows('#inventory',bx.inventory);rows('#market',bx.market)}
function setupBx(){renderBizXtreme();$('#starterPack').onclick=()=>{localStorage.setItem('chimera-starter-pack','claimed');log('Frontier Starter Pack marked claimed locally.');alert('Starter Pack claimed locally.');};$('#newSave').onclick=()=>{const save={version:1,tick:0,score:0,xp:0,expedition:0,createdAt:new Date().toISOString()};put('saves',{id:'bizxtreme-current',...save});log('New BizXtreme local save created.');}}
function renderControls(){const el=$('#controlEditor');el.innerHTML=Object.entries(controls).map(([k,v])=>'<div class="bind"><span>'+esc(k)+'</span><button data-bind="'+esc(k)+'">'+esc(v)+'</button></div>').join('');$$('[data-bind]').forEach(b=>b.onclick=()=>{listenAction=b.dataset.bind;b.classList.add('listening');b.textContent='Press key…'})}
function setupControls(){renderControls();window.addEventListener('keydown',async e=>{if(!listenAction)return;e.preventDefault();controls[listenAction]=e.code;await put('controls',{id:'default',bindings:controls});listenAction=null;renderControls();$('#mameInputPanel').innerHTML='<div class="control-grid">'+Object.entries(controls).map(([k,v])=>'<div><strong>'+esc(k)+'</strong><br><span class="muted">'+esc(v)+'</span></div>').join('')+'</div>';log('Bound '+e.code)});$('#resetControls').onclick=()=>{Object.assign(controls,{up:'ArrowUp',down:'ArrowDown',left:'ArrowLeft',right:'ArrowRight',fire1:'KeyZ',fire2:'KeyX',start:'Enter',select:'ShiftLeft',menu:'Tab',pause:'Escape',virtualKeyboard:'F12',save:'F5',load:'F7'});put('controls',{id:'default',bindings:controls});renderControls();log('Controls reset.')}}
async function databaseView(){const [m,g,s,c]=await Promise.all([all('machines'),all('games'),all('saves'),all('controls')]);$('#dbSummary').innerHTML='<div class="chips"><span>Machines: '+m.length+'</span><span>Games: '+g.length+'</span><span>Saves: '+s.length+'</span><span>Profiles: '+c.length+'</span><span>IndexedDB v3</span></div>'}
async function exportDB(){const out={version:3,exportedAt:new Date().toISOString(),machines:await all('machines'),games:await all('games'),saves:await all('saves'),controls:await all('controls')};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(out,null,2)],{type:'application/json'}));a.download='chimera-ii-database.json';a.click();log('Database exported.')}
function setupDB(){$('#exportDb').onclick=exportDB;$('#importDb').onclick=()=>$('#dbFile').click();$('#dbFile').onchange=async()=>{const f=$('#dbFile').files[0];if(!f)return;const o=JSON.parse(await f.text());for(const n of ['machines','games','saves','controls'])for(const x of o[n]||[])await put(n,x);log('Database imported.');databaseView()};databaseView()}
function setupAmiga(){const c=[['Joystick','D-pad / left stick'],['Mouse','Right stick'],['Fire 1','Z / A'],['Fire 2','X / B'],['Virtual keyboard','F12 / Select'],['Status bar','F11 / Select long']];$('#amigaControls').innerHTML=c.map(x=>'<div><strong>'+esc(x[0])+'</strong><br><span class="muted">'+esc(x[1])+'</span></div>').join('');$('#amigaDetect').onclick=checkBridge;$('#amigaLaunch').onclick=async()=>{if(!await checkBridge())return;try{await bridge('/launch/amiga',{model:$('#amigaModel').value,video:$('#amigaVideo').value,lineMode:$('#amigaLine').value,content:$('#amigaContent').value});log('Amiga local launch requested.')}catch(e){alert('Local Amiga launch failed: '+e.message)}}}
async function boot(){setupNav();await openDB();await initDBData();overview();setupMame();setupGames();renderBizx();setupBx();setupControls();setupDB();setupAmiga();await checkBridge();log('Aurora Control Center ready. Artwork: '+ART)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();