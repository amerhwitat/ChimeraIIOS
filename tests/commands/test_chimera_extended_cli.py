#!/usr/bin/env python3
"""Runtime smoke tests for newly staged source-backed Chimera command frontends."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def run(*args, input_text=None):
    return subprocess.run(args,input=input_text,text=True,capture_output=True)

nbit=run(sys.executable,str(ROOT/"tools/runtime/chimera-nbit-mode.py"),
         "--width","128","--operation","add","--lhs","1","--rhs","2","--json")
assert nbit.returncode==0,(nbit.stdout,nbit.stderr)
nbit_json=json.loads(nbit.stdout)
assert nbit_json["width_bits"]==128 and nbit_json["result"]=="0x3"
assert nbit_json["hardware_native"] is False and nbit_json["execution"]=="software-reference"

risc=run(sys.executable,str(ROOT/"tools/isa/riscv_codec.py"),"encode","ADDI x1, x0, 5")
assert risc.returncode==0,(risc.stdout,risc.stderr)
assert risc.stdout.strip()=="0x00500093"

components=run(sys.executable,str(ROOT/"tools/commands/chimera-componentctl.py"),"koronos","list")
assert components.returncode==0,(components.stdout,components.stderr)
assert "koronos.service" in json.loads(components.stdout).values()

with tempfile.TemporaryDirectory() as tmp:
    src=Path(tmp)/"rv.s";src.write_text("ADDI x1, x0, 5\n",encoding="utf-8")
    out=Path(tmp)/"rv.bin"
    hybrid=run(sys.executable,str(ROOT/"tools/commands/chimera-hybrid.py"),
               "assemble","--arch","riscv64","--input",str(src),"--output",str(out))
    assert hybrid.returncode==0,(hybrid.stdout,hybrid.stderr)
    assert out.read_bytes()==bytes.fromhex("93005000")

rnn=run(sys.executable,str(ROOT/"tools/commands/chimera-rnn.py"),"step",
        "--size","4","--features","0.25","0.5")
assert rnn.returncode==0,(rnn.stdout,rnn.stderr)
assert len(json.loads(rnn.stdout)["state"])==4

vector=run(sys.executable,str(ROOT/"tools/commands/chimera-math.py"),"vector","dot",
           "--a","[1,2,3]","--b","[4,5,6]")
assert vector.returncode==0,(vector.stdout,vector.stderr)
assert json.loads(vector.stdout)["result"]==32

matrix=run(sys.executable,str(ROOT/"tools/commands/chimera-math.py"),"tensor","matmul",
           "--a","[[1,2],[3,4]]","--b","[[5,6],[7,8]]")
assert matrix.returncode==0,(matrix.stdout,matrix.stderr)
assert json.loads(matrix.stdout)["result"]==[[19.0,22.0],[43.0,50.0]]

vec128=[1.0]*128
v128=run(sys.executable,str(ROOT/"tools/commands/chimera-math.py"),"128d","norm",
         "--a",json.dumps(vec128))
assert v128.returncode==0,(v128.stdout,v128.stderr)
assert json.loads(v128.stdout)["dimension"]==128

hdc=run(sys.executable,str(ROOT/"tools/commands/chimera-math.py"),"hdc","encode",
        "--text","Chimera 128D","--dimension","128")
assert hdc.returncode==0,(hdc.stdout,hdc.stderr)
hdc_data=json.loads(hdc.stdout)
assert len(hdc_data["bits"])==128 and set(hdc_data["bits"])<={"0","1"}
bound=run(sys.executable,str(ROOT/"tools/commands/chimera-math.py"),"hdc","bind",
          "--a",hdc_data["bits"],"--b",hdc_data["bits"])
assert bound.returncode==0 and json.loads(bound.stdout)["bits"]=="0"*128

neural=run(sys.executable,str(ROOT/"tools/commands/chimera-rnn.py"),"info")
assert neural.returncode==0 and json.loads(neural.stdout)["execution"]=="deterministic-reference"

encoded=run(sys.executable,str(ROOT/"tools/commands/chimera-p2p.py"),"encode",
            "--node-id","test-node","--kind","hello","--sequence","1",
            "--payload",'{"message":"hello"}',"--capability","frame-v1")
assert encoded.returncode==0,(encoded.stdout,encoded.stderr)
decoded=run(sys.executable,str(ROOT/"tools/commands/chimera-p2p.py"),"decode",input_text=encoded.stdout)
assert decoded.returncode==0,(decoded.stdout,decoded.stderr)
message=json.loads(decoded.stdout)
assert message["node_id"]=="test-node" and message["payload"]["message"]=="hello"

with tempfile.TemporaryDirectory() as tmp:
    source=Path(tmp)/"corpus.json"
    model=Path(tmp)/"model.json"
    source.write_text(json.dumps({"sentences":["chimera kernel","aurora desktop"]}),encoding="utf-8")
    trained=run(sys.executable,str(ROOT/"tools/cognition/trainable_rnn_lm.py"),
                "train","--source",str(source),"--output",str(model),"--epochs","1","--hidden","4")
    assert trained.returncode==0,(trained.stdout,trained.stderr)
    assert model.is_file()
    scored=run(sys.executable,str(ROOT/"tools/cognition/trainable_rnn_lm.py"),
               "score","--model",str(model),"--text","chimera")
    assert scored.returncode==0,(scored.stdout,scored.stderr)
    assert "score" in json.loads(scored.stdout)

build=(ROOT/"tools/commands/build-chimera-native-tools.sh").read_text(encoding="utf-8")
assert "userspace/hive/registryctl.cpp" in build and "userspace/hive/registry_store.cpp" in build
assert 'ln -sfn chimera-registry "$OUT/hivectl"' in build
manifest=(ROOT/"tools/commands/generate_runtime_manifest.py").read_text(encoding="utf-8")
for name in ("chimera","chmctl","chimera-registry","hivectl","chimera-nbit",
             "chimera-risc","chimera-llm","chimera-rnn","chimera-p2p",
             "chimera-install","chimera-apache","chimera-ss64","chimera-128d","chimera-vector","chimera-tensor","chimera-hdc","chimera-neural","chimera-shell-ar",
    "aegisctl","auroractl","jasperctl","koronosctl","nucleusctl","spitfirectl","spotnikctl",
    "chimera-security","chimera-live","chimera-hybrid"):
    assert f'"{name}": "/usr/bin/{name}"' in manifest, f"runtime manifest missing {name}"
stage=(ROOT/"tools/commands/stage-native-script-providers.py").read_text(encoding="utf-8")
for name in ("chimera-nbit","chimera-risc","chimera-llm","chimera-rnn",
             "chimera-p2p","chimera-install","chimera-apache","chimera-ss64",
             "chimera-128d","chimera-vector","chimera-tensor","chimera-hdc","chimera-neural"):
    assert f'"{name}":' in stage, f"staging map missing {name}"
print("PASS source-backed N-bit, RV32I, RNN, P2P, Hive and installer/Apache command providers")
