(()=>{'use strict';
window.ChimeraMameWeb={running:false,scriptUrl:null,wasmUrl:null,
 async start({js,wasm,roms=[],machine=''}){
  if(!js||!wasm)throw Error('A matching MAME Emscripten JavaScript and WASM pair is required.');
  this.stop();
  const wasmBlob=wasm.blob instanceof Blob?wasm.blob:new Blob([wasm.blob]);
  const jsBlob=js.blob instanceof Blob?js.blob:new Blob([js.blob],{type:'text/javascript'});
  this.wasmUrl=URL.createObjectURL(wasmBlob);this.scriptUrl=URL.createObjectURL(jsBlob);
  const files=[];for(const r of roms){const data=new Uint8Array(await r.blob.arrayBuffer());files.push({name:r.name,data});}
  const canvas=document.getElementById('mameCanvas');
  if(!canvas)throw Error('MAME canvas is missing.');
  const output=t=>{const el=document.getElementById('mameRuntimeStatus');if(el)el.textContent=String(t||'MAME WebAssembly runtime active');};
  window.Module={canvas,arguments:machine?['-rompath','/roms',machine]:['-rompath','/roms'],locateFile:(path,prefix)=>path.endsWith('.wasm')?this.wasmUrl:(prefix||'')+path,print:output,printErr:t=>output('MAME: '+t),preRun:[()=>{if(!window.Module.FS)return;try{window.Module.FS.mkdir('/roms')}catch{}for(const f of files){const safe=f.name.replace(/[^a-zA-Z0-9._-]/g,'_');try{window.Module.FS.writeFile('/roms/'+safe,f.data)}catch(e){output('ROM mount failed: '+e.message)}}}]};
  const s=document.createElement('script');s.src=this.scriptUrl;s.async=false;s.onload=()=>{this.running=true;output('MAME WebAssembly runtime loaded · build-specific controls may be required')};s.onerror=()=>output('MAME WebAssembly JavaScript failed to initialize');document.head.appendChild(s);
 },
 stop(){if(this.scriptUrl)URL.revokeObjectURL(this.scriptUrl);if(this.wasmUrl)URL.revokeObjectURL(this.wasmUrl);this.scriptUrl=this.wasmUrl=null;this.running=false;if(window.Module)try{window.Module.noExitRuntime=false}catch{}}
};})();