#!/usr/bin/env python3
"""Safe AI capability planner; optional runtimes are never auto-installed."""
import argparse, json

def choose(workload, devices):
    device=max(devices, key=lambda d:(2 if d.get('accelerator') else 0,d.get('compute_units',1)), default={'device':'cpu','compute_units':1})
    if workload.get('mixture_of_experts'): strategy='mixture_of_experts'
    elif workload.get('distributed'): strategy='distributed'
    elif workload.get('memory_constrained') and workload.get('model_parameters',0)>1_000_000_000: strategy='quantized'
    elif workload.get('latency_sensitive') and workload.get('context_tokens',0)>128: strategy='speculative'
    elif workload.get('streaming'): strategy='streaming'
    elif workload.get('batch_size',1)>1: strategy='batched'
    else: strategy='eager'
    return {'strategy':strategy,'device':device.get('device','cpu'),'parallel_units':max(1,int(device.get('compute_units',1))),'offload':bool(device.get('accelerator',False))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    result=choose({'latency_sensitive':True,'context_tokens':512},[{'device':'cpu','compute_units':8},{'device':'npu','compute_units':16,'accelerator':True}])
    print(json.dumps(result,indent=2) if args.json else f"{result['strategy']} on {result['device']} ({result['parallel_units']} units)")
if __name__=='__main__': main()
