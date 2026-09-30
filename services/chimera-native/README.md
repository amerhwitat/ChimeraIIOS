# Native Chimera Services staging

The authoritative service definitions live under `config/services/`. The ISO builder's existing `stage_features` phase copies the `services/` tree into `/system/`. This directory contains the staging contract and runtime documentation; the authoritative JSON must not be edited here.

Target installed systems must materialize the same registry at `/etc/chimera/services/` during installation. The installer service-selection metadata is staged from `installer/services/`.
