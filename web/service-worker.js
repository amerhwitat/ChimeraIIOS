const CACHE='chimera-web-v1';
const CORE=['./','./index.html','./style.css','./aurora_shell.css','./chimera-hub.css','./chimera-hub.js','./mame-web-runtime.js','./desktop_profiles.json','./aurora_webgl_desktops.html','./aurora_webgl_desktops.css','./aurora_webgl_desktops.js','./aurora_3d_desktop.html','./aurora_3d_desktop.css','./aurora_3d_desktop.js','./pdf-reader.html','./pdf-reader.css','./pdf-reader.js','./ancient-ocr.html','./ancient-ocr.css','./ancient-ocr.js','./network.html'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  const u=new URL(event.request.url);
  if(u.origin!==self.location.origin||event.request.method!=='GET')return;
  event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(event.request,copy)).catch(()=>{});}return r;}).catch(()=>caches.match('./index.html'))));
});