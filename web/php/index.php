<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
$payload=['application'=>'Chimera II OS','webImplementation'=>'PHP standalone','capabilities'=>['api','dashboard','json']];
echo json_encode($payload, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
