# Mobile Driver Architecture

Drivers are isolated from the portable kernel core and communicate through capability-controlled interfaces.

Planned driver families:

- display and composition;
- touchscreen/input;
- GPU and accelerator;
- audio;
- camera;
- IMU, proximity, ambient-light and other sensors;
- UFS/eMMC/NVMe-class storage;
- USB/USB-C;
- Wi-Fi and Bluetooth;
- cellular modem;
- power-management and battery/charger;
- IOMMU/DMA.

Each driver should expose a narrow service contract and keep hardware-specific register programming in its platform implementation.
