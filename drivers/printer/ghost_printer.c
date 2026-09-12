#include <stdio.h>
#include <string.h>

/* Ghost printer: a deterministic virtual printer sink. It accepts text/PS-like
   byte streams and writes a portable output file. It never talks to hardware. */
int chm_ghost_printer_render(const char* input, const char* output_path) {
    if (!input || !output_path) return -1;
    FILE* out = fopen(output_path, "wb");
    if (!out) return -2;
    const char header[] = "%CHIMERA-GHOST-PRINTER-1\n";
    fwrite(header, 1, sizeof(header) - 1, out);
    fwrite(input, 1, strlen(input), out);
    fclose(out);
    return 0;
}

#ifdef CHM_GHOST_PRINTER_STANDALONE
int main(int argc, char** argv) {
    if (argc != 3) return 64;
    return chm_ghost_printer_render(argv[1], argv[2]);
}
#endif
