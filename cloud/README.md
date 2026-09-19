# Chimera II OS Cloud & Cluster Fabric

The Cloud Fabric provides a provider-neutral layer for running Chimera II OS workloads and VM images on local virtualization, Kubernetes, OpenShift/OKD, OpenStack, and major public-cloud infrastructure.

## Targets

- `local`: CVEL/QEMU, VirtualBox, VMware adapters
- `kubernetes`: Kubernetes API and kubeadm-oriented node bootstrap
- `openshift`: OpenShift/OKD API and CLI (`oc`) integration
- `openstack`: OpenStack Nova/Glance/Neutron/Cinder via `openstack` CLI
- `aws`, `azure`, `gcp`: infrastructure adapters; credentials remain external to the repository

The adapters generate plans/manifests and execute only when explicitly requested. They do not silently download images, flash firmware, or create billable cloud resources.

## Chimera II OS installation model

The Kubernetes/OpenShift/OpenStack clients are installed as host-side administration applications. A Chimera II OS image can then be used as a VM/node image where the selected platform supports the required architecture and kernel/container-runtime prerequisites.

Kubernetes self-managed clusters require a supported Linux environment, a container runtime, kubelet/kubeadm/kubectl and cluster networking. See the official Kubernetes documentation for current version requirements. OpenShift/OKD installation is provider/platform-specific and should use the corresponding installer and release artifacts.

## Commands

```text
chimera-cloud providers
chimera-cloud doctor kubernetes
chimera-cloud doctor openshift
chimera-cloud doctor openstack
chimera-cloud plan kubernetes
chimera-cloud plan openshift
chimera-cloud plan openstack
chimera-cloud apply --provider <provider> --plan <file>
```

`apply` is intentionally explicit because it may create infrastructure or modify a cluster.
