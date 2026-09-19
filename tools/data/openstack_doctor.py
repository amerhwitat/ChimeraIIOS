#!/usr/bin/env python3
import json, shutil
services=['keystone','nova','neutron','glance','cinder','swift','ironic','manila','heat']
cli=bool(shutil.which('openstack'))
print(json.dumps({'ecosystem':'openstack','cli_available':cli,'services':services,'mode':'read-only discovery; credentials are supplied by the OpenStack client environment'},indent=2))
