(()=>{"use strict";
const $=id=>document.getElementById(id);let data=null;
const BRIDGE="http://127.0.0.1:8765";
const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function bridge(path,body){return fetch(BRIDGE+path,{method:body?"POST":"GET",headers:{"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined,cache:"no-store"}).then(async r=>{const t=await r.text();let j={};try{j=t?JSON.parse(t):{}}catch{}if(!r.ok)throw Error(j.error||t||("HTTP "+r.status));return j})}
async function detect(id,el){
 try{const x=await bridge("/emulators/status",{id});el.textContent=x.installed?"installed":"not installed";el.dataset.state=x.installed?"ready":"missing"}
 catch{el.textContent="local bridge offline";el.dataset.state="offline"}
}
async function launch(id,el){
 const media=prompt("Enter the local game/disc path you are entitled to use:",localStorage.getItem("chimera-ps-media-"+id)||"");
 if(!media)return;
 localStorage.setItem("chimera-ps-media-"+id,media);
 el.disabled=true;const old=el.textContent;el.textContent="Launching…";
 try{await bridge("/launch/emulator",{id,media});el.textContent="Launch requested";el.dataset.state="ready"}
 catch(e){el.textContent="Adapter unavailable";el.title=e.message;alert("PlayStation adapter: "+e.message)}
 finally{setTimeout(()=>{el.disabled=false;el.textContent=old},2200)}
}
function render(){
 if(!data)return;
 const q=$("filter").value.toLowerCase(),g=$("generation").value,cards=[];
 data.generations.forEach(gen=>{if(g&&gen.id!==g)return;gen.emulators.forEach(e=>{
  const hay=(gen.title+" "+e.title+" "+e.id+" "+e.status).toLowerCase();if(q&&!hay.includes(q))return;
  cards.push({gen,e})
 })});
 $("grid").innerHTML=cards.map(x=>{
  const gen=x.gen,e=x.e,req=(e.requirements||[]).concat(e.bios_required?["user BIOS"]:[],e.firmware_required?["user firmware"]:[]);
  return '<article class="card '+(e.status==="recommended"?"recommended":"")+'"><div><span class="eyebrow">'+esc(gen.title)+'</span><h2>'+esc(e.title)+'</h2></div><div class="meta"><span class="pill">'+esc(e.status)+'</span><span class="pill">'+esc(e.kind)+'</span><span class="pill">'+esc(e.license)+'</span></div><div class="emu"><div class="emu-head"><span class="emu-title">Aurora adapter</span><span class="status" data-id="'+esc(e.id)+'">checking…</span></div><div class="details">Platforms: '+esc((e.platforms||[]).join(", "))+'<br>Media: '+esc((e.media||[]).join(", "))+'<br>'+(req.length?"Requirements: "+esc(req.join(", ")):"No external firmware declared.")+'</div><div class="buttons"><button data-launch="'+esc(e.id)+'">Launch local</button><button data-detect="'+esc(e.id)+'">Detect</button><a href="'+esc(e.source)+'" target="_blank" rel="noopener">Source</a><a href="'+esc(e.website)+'" target="_blank" rel="noopener">Project site</a></div></div></article>'
 }).join("");
 $("grid").querySelectorAll("[data-detect]").forEach(b=>b.onclick=()=>detect(b.dataset.detect,$("grid").querySelector('[data-id="'+CSS.escape(b.dataset.detect)+'"]')));
 $("grid").querySelectorAll("[data-launch]").forEach(b=>b.onclick=()=>launch(b.dataset.launch,b));
 $("grid").querySelectorAll("[data-id]").forEach(x=>detect(x.dataset.id,x))
}
$("filter").oninput=render;$("generation").onchange=render;
$("fullscreen").onclick=()=>document.documentElement.requestFullscreen?.();
$("notice").innerHTML="<div><b>Runtime boundary:</b> GitHub Pages is static. Detection and launching use the optional localhost Chimera bridge; without it, source/catalog controls remain fully usable. Use only games and system software you are entitled to use.</div>";
fetch("playstation_emulators.json",{cache:"no-store"}).then(r=>r.json()).then(x=>{data=x;render()}).catch(e=>$("grid").innerHTML="<article class=card>Manifest load failed: "+esc(e.message)+"</article>");
})();