from dataclasses import dataclass

@dataclass(frozen=True)
class DeviceFamily:
    vendor: str
    stacks: tuple[str, ...]

GPU_FAMILIES = (
    DeviceFamily("NVIDIA", ("nouveau", "vendor-adapter", "CUDA-adapter")),
    DeviceFamily("AMD", ("amdgpu", "radeon", "ROCm-adapter")),
    DeviceFamily("Intel", ("i915", "xe", "Level-Zero-adapter")),
    DeviceFamily("Apple", ("Metal-adapter",)),
    DeviceFamily("ARM Mali", ("Mali-adapter",)),
    DeviceFamily("Qualcomm Adreno", ("Freedreno", "Turnip-adapter")),
    DeviceFamily("Imagination PowerVR", ("PowerVR-adapter",)),
    DeviceFamily("3dfx/Matrox/S3/VIA/SiS", ("legacy-display-adapter",)),
    DeviceFamily("Virtual", ("virtio-gpu", "VMware-SVGA", "QXL")),
)

PRINTER_PROTOCOLS = ("IPP", "PostScript", "PCL5", "PCL6", "ESC/P", "ESC/POS", "PDF", "Ghost")
