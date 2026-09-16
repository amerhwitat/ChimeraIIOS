# Chimera II OS Cloud Fabric Operations

## Discovery
Use `chimera-cloud providers` and `chimera-cloud doctor <provider>` to inspect configured provider tooling. Discovery never changes infrastructure.

## Planning
Create a provider plan with `chimera-cloud plan <provider> --output <file>`. Plans use `CHIMERA-PLAN-1`, keep credentials external, and are intended for review before any deployment gate.

## Kubernetes
Install the client/node packages with `tools/installer/install_kubernetes.sh` on supported Debian/Ubuntu-compatible Chimera installations. Initialize or join a cluster separately with the administrator's chosen kubeadm configuration. Workloads are represented by manifests under `infrastructure/kubernetes`.

## OpenShift
Use `tools/installer/install_openshift_tools.sh` for host preparation. Select `oc` and `openshift-install` versions matching the target OpenShift/OKD release. Cluster installation remains an explicit platform operation.

## OpenStack
The Terraform module under `infrastructure/openstack` accepts explicit image, flavor, and network identifiers. Volumes and floating IPs are opt-in. Supply OpenStack authentication through the normal external environment/configuration; never commit credentials.

## Public clouds
AWS, Azure, and GCP adapters provide discovery and plan contracts. Live provider execution belongs in protected CI environments with explicit credentials and approval.

## VM safety
Guest images must be explicitly selected and architecture checked before execution. CVEL command construction is argv-based and does not implicitly download firmware or images.
