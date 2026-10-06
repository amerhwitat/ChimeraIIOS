const state={apps:[],favorites:new Set(JSON.parse(localStorage.getItem("chimera.portfolio.favorites")||"[]")),sort:"name"};
const $=s=>document.querySelector(s);
async function loadApps(){try{const r=await fetch("portfolio-manifest.json",{cache:"no-store"});if(!r.ok)throw new Error("manifest "+r.status);const m=await r.json();state.apps=Array.isArray(m.apps)?m.apps:[]}catch(e){state.apps=[];$("#apps").innerHTML='<div class="empty">Application manifest could not be loaded. Open the Aurora Control Center and retry.</div>';return}buildCategories();render()}
function buildCategories(){const select=$("#category");select.querySelectorAll("option:not(:first-child)").forEach(x=>x.remove());[...new Set(state.apps.map(a=>a.category))].sort().forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;select.append(o)})}
function render(){const q=$("#search").value.toLowerCase().trim(),cat=$("#category").value,onlyFav=$("#favoritesOnly").checked,sort=$("#sort").value;
let list=state.apps.filter(a=>(!q||[a.name,a.repository,a.description,...a.tags].join(" ").toLowerCase().includes(q))&&(cat==="all"||a.category===cat)&&(!onlyFav||state.favorites.has(a.id)));
list.sort((a,b)=>sort==="category"?a.category.localeCompare(b.category)||a.name.localeCompare(b.name):a.name.localeCompare(b.name));
$("#count").textContent=`${list.length} of ${state.apps.length} applications`;
$("#apps").innerHTML=list.length?list.map(card).join(""):'<div class="empty">No matching applications.</div>';
$("#favoriteCount").textContent=state.favorites.size;
}
function card(a){const fav=state.favorites.has(a.id);return `<article class="card"><div class="meta">${esc(a.category)} · ${esc(a.repository)}</div><div class="title-row"><h2>${esc(a.name)}</h2><button class="icon" data-fav="${esc(a.id)}" aria-label="${fav?"Remove from favorites":"Add to favorites"}">${fav?"★":"☆"}</button></div><p>${esc(a.description)}</p><div class="tags">${a.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join("")}</div><div class="actions"><a class="primary" href="${esc(a.portal)}">Open in Web UI</a><a href="${esc(a.source)}" target="_blank" rel="noopener">Source</a></div></article>`}
function esc(v){return String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
document.addEventListener("input",e=>{if(e.target.matches("#search"))render()});
document.addEventListener("change",e=>{if(e.target.matches("#category,#sort,#favoritesOnly"))render()});
document.addEventListener("click",e=>{const b=e.target.closest("[data-fav]");if(!b)return;const id=b.dataset.fav;if(state.favorites.has(id))state.favorites.delete(id);else state.favorites.add(id);localStorage.setItem("chimera.portfolio.favorites",JSON.stringify([...state.favorites]));render()});
document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();$("#search").focus()}});
loadApps();