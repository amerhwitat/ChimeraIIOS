import { WebSocketServer } from 'ws';

const HOST = process.env.CHIMERA_SIGNAL_HOST || '127.0.0.1';
const PORT = Number(process.env.CHIMERA_SIGNAL_PORT || 8780);
const MAX = 64 * 1024;
const rooms = new Map();

function room(name) {
  if (!rooms.has(name)) rooms.set(name, new Map());
  return rooms.get(name);
}
function cleanPeer(peer) {
  return { id:String(peer?.id||''), nick:String(peer?.nick||'Chimera').slice(0,32), avatar:String(peer?.avatar||'✦').slice(0,8), game:String(peer?.game||'').slice(0,64) };
}
function send(ws,msg) {
  if (ws.readyState === ws.OPEN) ws.send(JSON.stringify(msg));
}
function broadcast(r,msg,except) {
  for (const [id,entry] of r) if (entry.ws!==except) send(entry.ws,msg);
}
function remove(ws) {
  const meta=ws.__chimera;
  if (!meta) return;
  const r=rooms.get(meta.room);
  if (!r) return;
  r.delete(meta.id);
  broadcast(r,{type:'leave',id:meta.id});
  if (!r.size) rooms.delete(meta.room);
  ws.__chimera=null;
}

const wss=new WebSocketServer({host:HOST,port:PORT,maxPayload:MAX});
wss.on('connection',(ws)=>{
  ws.on('error',()=>{});
  ws.on('close',()=>remove(ws));
  ws.on('message',(raw)=>{
    if (raw.length>MAX) return ws.close(1009,'message too large');
    let m; try{m=JSON.parse(raw.toString())}catch{return send(ws,{type:'error',error:'invalid-json'});}
    if (m.type==='join') {
      const id=String(m.peer?.id||m.id||'');
      const roomName=String(m.room||'chimera-public').slice(0,96);
      if(!id)return send(ws,{type:'error',error:'peer-id-required'});
      remove(ws);
      const r=room(roomName);
      if(r.size>=256)return send(ws,{type:'error',error:'room-full'});
      const peer=cleanPeer({...m.peer,id});
      ws.__chimera={id,room:roomName,peer};
      const peers=[...r.values()].map(x=>x.peer);
      r.set(id,{ws,peer});
      send(ws,{type:'peers',room:roomName,peers});
      broadcast(r,{type:'presence',...peer,room:roomName},ws);
      return;
    }
    const meta=ws.__chimera;
    if(!meta)return send(ws,{type:'error',error:'join-required'});
    const r=rooms.get(meta.room);
    if(!r)return;
    if(['offer','answer','candidate'].includes(m.type)){
      const to=String(m.to||'');
      const target=r.get(to);
      if(!target)return send(ws,{type:'error',error:'peer-not-found',to});
      send(target.ws,{...m,from:meta.id,room:meta.room});
      return;
    }
    if(m.type==='presence'){
      const peer=cleanPeer({...meta.peer,...m,id:meta.id});
      meta.peer=peer;
      r.set(meta.id,{ws,peer});
      broadcast(r,{type:'presence',...peer,room:meta.room},ws);
      return;
    }
    if(m.type==='peers') send(ws,{type:'peers',room:meta.room,peers:[...r.values()].map(x=>x.peer)});
  });
});

console.log('Chimera II signaling relay: ws://'+HOST+':'+PORT);
console.log('Opt-in relay only; it does not scan the network or inspect WebRTC SDP/ICE payloads.');