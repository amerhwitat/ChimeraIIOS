#!/usr/bin/env python3
"""Safe IoT endpoint/topic planner; network access is never implicit."""
import argparse, json
ALLOWED_SCHEMES=('mqtt://','mqtts://','opc.tcp://','coap://','coaps://')
def valid_endpoint(endpoint): return bool(endpoint) and len(endpoint)<=255 and ' ' not in endpoint and '..' not in endpoint and endpoint.startswith(ALLOWED_SCHEMES)
def valid_topic(topic): return bool(topic) and len(topic)<=256 and not any(ord(c)<32 for c in topic)
def plan(protocol,endpoint,write=False): return {'protocol':protocol,'endpoint':endpoint,'valid_endpoint':valid_endpoint(endpoint),'write_requested':write,'network_connect':False,'device_write':False}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',default='mqtt5'); ap.add_argument('--endpoint',default='mqtts://localhost'); ap.add_argument('--write',action='store_true'); args=ap.parse_args(); print(json.dumps(plan(args.protocol,args.endpoint,args.write),indent=2))
if __name__=='__main__': main()
