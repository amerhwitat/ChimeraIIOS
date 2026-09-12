const state={edition:'computer',registerBits:8192,ipcSamples:0};
const app=document.querySelector('#app');
function render(){app.innerHTML=`<article><h2>${state.edition} edition</h2><p>Register width: ${state.registerBits} bits</p><button id="sample">Record IPC sample</button><output id="out">Samples: ${state.ipcSamples}</output></article>`;document.querySelector('#sample').onclick=()=>{state.ipcSamples++;render()}}
render();
if('serviceWorker' in navigator) navigator.serviceWorker.register('../pwa/sw.js').catch(()=>{});