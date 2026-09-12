namespace Chimera.Hardware;
public static class Registry {
    public static readonly string[] GpuFamilies = {
        "NVIDIA", "AMD", "Intel", "Apple", "ARM Mali", "Qualcomm Adreno",
        "Imagination PowerVR", "3dfx", "Matrox", "S3", "VIA", "SiS", "Virtual"
    };
    public static readonly string[] PrinterProtocols = { "IPP", "PostScript", "PCL5", "PCL6", "ESC/P", "ESC/POS", "PDF", "Ghost" };
}
