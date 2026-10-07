<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
$id = isset($_GET['id']) ? preg_replace('/[^a-zA-Z0-9_-]/', '', (string)$_GET['id']) : '';
$map = [
  'duckstation'=>['duckstation','duckstation-qt'],'mednafen'=>['mednafen'],
  'beetle-psx'=>['retroarch'],'pcsx-rearmed'=>['retroarch'],'swanstation'=>['retroarch'],
  'pcsx2'=>['pcsx2','pcsx2-qt'],'play'=>['play','Play'],'rpcs3'=>['rpcs3'],
  'shadps4'=>['shadps4','shadPS4','shadps4-qt'],'rpcsx'=>['rpcsx'],
  'fpps4'=>['fpPS4','fpps4'],'kytyps5'=>['kyty_emulator','KytyPS5'],'rpcsx-ps5'=>['rpcsx']
];
$found=null;
foreach(($map[$id]??[]) as $name){
  $cmd=trim((string)@shell_exec('command -v '.escapeshellarg($name).' 2>/dev/null'));
  if($cmd!==''){ $found=$cmd; break; }
}
echo json_encode(['id'=>$id,'installed'=>$found!==null,'executable'=>$found,'status'=>$found?'installed':'not installed']);
