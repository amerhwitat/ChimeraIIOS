#!/usr/bin/env python3
"""Start only explicitly reviewed enterprise services that have installed units."""
import json, os, shutil, subprocess, sys
from pathlib import Path
PLAN=Path(os.environ.get("CHIMERA_ENTERPRISE_PLAN","/etc/chimera/enterprise-services.plan.json"))
UNITS={
 "postgresql":["postgresql.service"],"mariadb":["mariadb.service"],"redis":["redis-server.service","redis.service"],
 "nginx":["nginx.service"],"apache":["apache2.service","httpd.service"],"haproxy":["haproxy.service"],
 "prometheus":["prometheus.service"],"grafana":["grafana-server.service","grafana.service"],"loki":["loki.service"],
 "containerd":["containerd.service"],"podman":["podman.service"],"kubernetes-tools":[],
 "samba":["smbd.service","samba.service"],"cups":["cups.service"],"openssh":["sshd.service","ssh.service"],
 "restic":[],"borgbackup":[],"rabbitmq":["rabbitmq-server.service"],"mosquitto":["mosquitto.service"],
 "ldap":["slapd.service"],"kerberos":["krb5-kdc.service","krb5kdc.service"],"sso":["keycloak.service"]
}
def main():
    if not PLAN.is_file(): return 0
    try: plan=json.loads(PLAN.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"enterprise plan rejected: {e}",file=sys.stderr); return 2
    if plan.get("user_review_confirmed") is not True:
        print("enterprise services not started: installer review not confirmed"); return 0
    enabled=set(plan.get("enabled_targets",[]))
    selected=plan.get("services",[])
    systemctl=shutil.which("systemctl")
    native=shutil.which("chimera-service")
    for item in selected:
        sid=item.get("id")
        if not isinstance(sid,str) or sid not in UNITS: continue
        if item.get("boot_target") not in enabled: continue
        if item.get("staging") not in ("package payloads extracted; dependency resolution, service configuration and ABI conversion still require rootfs integration",
                                       "verified source build commands completed with DESTDIR staging; review package ABI and service config before enabling"):
            continue
        if native:
            rc=subprocess.run([native,"start",sid],check=False,timeout=15).returncode
            if rc==0: continue
        if systemctl:
            for unit in UNITS[sid]:
                probe=subprocess.run([systemctl,"cat",unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
                if probe.returncode==0:
                    subprocess.run([systemctl,"start",unit],check=False,timeout=15)
                    break
    return 0
if __name__=="__main__": raise SystemExit(main())
