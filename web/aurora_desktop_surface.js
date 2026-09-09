(()=>{'use strict';
const windows=new Map();let z=300;
function createWindow(app){
  if(!app?.url)return null;
  const existing=windows.get(app.id);if(existing){existing.style.zIndex=++z;return existing}
  const w=document.createElement('section');w.className='aurora-window focused';w.dataset.app=app.id;w.style.left=(110+windows.size*28)+'px';w.style.top=(100+windows.size*24)+'px';w.style.width='760px';w.style.height='520px';w.style.zIndex=++z;
  w.innerHTML=`<header class="aurora-window-titlebar"><span class="aurora-window-title">${app.title}</span><span class="aurora-window-actions"><button data-min>—</button><button data-max>□</button><button data-close>×</button></span></header><div class="aurora-window-body"><iframe title="${app.title}" src="${app.url}" sandbox="allow-scripts allow-forms allow-same-origin"></iframe></div>`;
  document.body.append(w);windows.set(app.id,w);
  w.addEventListener('pointerdown',()=>{document.querySelectorAll('.aurora-window').forEach(x=>x.classList.remove('focused'));w.classList.add('focused');w.style.zIndex=++z});
  w.querySelector('[data-close]').onclick=()=>{windows.delete(app.id);w.remove()};
  w.querySelector('[data-min]').onclick=()=>{w.querySelector('.aurora-window-body').hidden=!w.querySelector('.aurora-window-body').hidden};
  w.querySelector('[data-max]').onclick=()=>{w.classList.toggle('maximized');if(w.classList.contains('maximized')){w.dataset.restore=JSON.stringify({left:w.style.left,top:w.style.top,width:w.style.width,height:w.style.height});Object.assign(w.style,{left:'88px',top:'76px',width:'calc(100vw - 390px)',height:'calc(100vh - 150px)'})}else{const r=JSON.parse(w.dataset.restore||'{}');Object.assign(w.style,r)}};
  const bar=w.querySelector('.aurora-window-titlebar');let drag=null;
  bar.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;drag={x:e.clientX,y:e.clientY,left:w.offsetLeft,top:w.offsetTop};bar.setPointerCapture(e.pointerId)});
  bar.addEventListener('pointermove',e=>{if(!drag)return;w.style.left=Math.max(72,drag.left+e.clientX-drag.x)+'px';w.style.top=Math.max(70,drag.top+e.clientY-drag.y)+'px'});
  bar.addEventListener('pointerup',()=>drag=null);
  return w;
}
window.ChimeraAuroraDesktop={open:createWindow,windows};
})();
