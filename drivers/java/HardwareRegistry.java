package chm.hardware;

public final class HardwareRegistry {
  public record GpuFamily(String vendor, String[] stacks) {}
  public static final GpuFamily[] GPUS = {
    new GpuFamily("NVIDIA", new String[]{"nouveau", "vendor-adapter", "CUDA-adapter"}),
    new GpuFamily("AMD", new String[]{"amdgpu", "radeon", "ROCm-adapter"}),
    new GpuFamily("Intel", new String[]{"i915", "xe", "Level-Zero-adapter"}),
    new GpuFamily("Apple", new String[]{"Metal-adapter"}),
    new GpuFamily("ARM Mali", new String[]{"Mali-adapter"}),
    new GpuFamily("Qualcomm Adreno", new String[]{"Freedreno", "Turnip-adapter"}),
    new GpuFamily("Imagination PowerVR", new String[]{"PowerVR-adapter"}),
    new GpuFamily("Legacy 3dfx/Matrox/S3/VIA/SiS", new String[]{"legacy-display-adapter"}),
    new GpuFamily("Virtual", new String[]{"virtio-gpu", "VMware-SVGA", "QXL"})
  };
  private HardwareRegistry() {}
}
