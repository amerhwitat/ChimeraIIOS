# Aurora Peripheral Support

Aurora now has an explicit user-requested peripheral capability model.

Camera support targets PipeWire with V4L2 and libcamera compatibility. PipeWire documents camera capture streams and V4L2/libcamera SPA APIs. The intended flow is: discover camera, ask the user for Allow Camera, request the capability from Koronos/Aegis, then open the selected backend.

The same boundary covers microphone/audio, keyboard and pointer input, HID, serial/USB, GPU/display, storage, Bluetooth, network, I2C/SPI, and printers.

The initial native client is aurora_peripherals:
- list
- request <device-id>
- camera <camera-device-id>

Discovery is deliberately separate from access. Finding a device never grants access automatically.
