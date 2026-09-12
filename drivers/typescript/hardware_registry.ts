export const gpuFamilies = ["NVIDIA","AMD","Intel","Apple","ARM Mali","Qualcomm Adreno","Imagination PowerVR","3dfx","Matrox","S3","VIA","SiS","Virtual"] as const;
export const printerProtocols = ["IPP","PostScript","PCL5","PCL6","ESC/P","ESC/POS","PDF","Ghost"] as const;
export type GpuFamily = typeof gpuFamilies[number];
