# Chimera II OS DevOps Fabric

The DevOps Fabric connects source generation, builds, tests, VM/image packaging, infrastructure planning, and cluster deployment.

## Pipeline

```text
source
  -> code generation
  -> static validation
  -> C/C++/ASM/Python build
  -> unit/integration tests
  -> CVEL VM/image validation
  -> artifact packaging
  -> IaC plan
  -> Kubernetes/OpenShift/OpenStack deployment gate
```

Deployment is deliberately an approval boundary. CI can produce plans and artifacts automatically; production infrastructure mutation requires an explicit deployment job/action and external credentials.

## Cluster targets

### Kubernetes

Use `kubeadm` for self-managed cluster bootstrap where appropriate, with a supported Linux host, container runtime, kubelet and CNI. Chimera provides installation and workload manifests but does not bundle Kubernetes into the kernel.

### OpenShift / OKD

Use the release-matched `oc` and `openshift-install` tooling and the installation method supported by the target platform. Chimera provides manifests and automation hooks that can be applied after cluster creation.

### OpenStack

OpenStack is treated as an IaaS target: Glance images, Nova instances, Neutron networking and Cinder storage can be provisioned through Terraform or the OpenStack CLI. Credentials are external and never generated into repository files.

## Code generation

Generated code and infrastructure plans are artifacts of a pipeline, not an automatic authority to deploy. The same policy applies to AI-assisted or template-generated source: generation is followed by compilation, tests and review gates.
