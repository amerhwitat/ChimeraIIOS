# OpenStack integration

Chimera integrates with OpenStack through the standard client/API boundary. The registry covers Keystone identity, Nova compute, Neutron networking, Glance images, Cinder block storage, Swift object storage, Ironic bare metal, Manila shared filesystems and Heat orchestration.

Use `tools/data/openstack_doctor.py` for local CLI discovery. Credentials are supplied through the OpenStack client environment/configuration and are never committed to Chimera manifests.

OpenStack operations are read-only by default in the Chimera diagnostics layer. Provisioning, deletion, networking changes and storage writes require an explicit higher-level operation and policy configuration.
