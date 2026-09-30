#!/usr/bin/env python3
"""Materialize a validated service plan into an installed Chimera target."""
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--plan',required=True)
    ap.add_argument('--target',required=True)
    args=ap.parse_args()
    plan=json.loads(Path(args.plan).read_text())
    target=Path(args.target)/'etc/chimera/services'
    target.mkdir(parents=True,exist_ok=True)
    (target/'selected-services.json').write_text(json.dumps(plan,indent=2)+'\n')
    (target/'INSTALLER-SELECTED').write_text('1\n')
    print(f'Materialized {len(plan.get("services",[]))} selected service(s) into {target}')

if __name__=='__main__': main()
