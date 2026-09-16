#!/usr/bin/env python3
import json, shutil
TOOLS=['hdfs','yarn','hive','hbase','spark-submit','tez','kafka-topics','ozone']
print(json.dumps({'ecosystem':'apache-hadoop','tools':[{ 'name':x,'available':bool(shutil.which(x))} for x in TOOLS]},indent=2))
