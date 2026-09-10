# AmigaGuruBook source record

**Supplied source:** `AmigaGuruBook[ENG]FullSearch(1).txt`

**SHA-256:** `2d194b4d9d0adfa7a0c3fa435cea24957025d9379f7d354dd30aebfee1e7d102`

The full source is a user-supplied 2.7 MB text reference attached to the Chimera II OS work. The repository records its provenance and extracts the portions required by the filesystem compatibility implementation rather than silently rewriting the source.

## Integrated findings

- DOS0 identifies Amiga OFS/old filesystem.
- DOS1 identifies Amiga FastFileSystem (FFS).
- DOS2 and DOS3 identify international OFS/FFS variants.
- The source documents Amiga-UNIX partition identifiers for classic AT&T System-V and Berkeley-on-System-V formats.
- CrossDOS is described as a filesystem handler and was the first filesystem to support the documented disk-startup packet used by DiskCopy in Workbench 2.1.
- Amiga filesystem handlers expose packet-based operations, volume identity, startup metadata, block allocation and filesystem-specific behavior; these motivate the Chimera foreign-handler compatibility API.

## Source-grounded excerpts used in the design

The supplied source identifies DOS0/DOS1/DOS2/DOS3 in the `de_DosType` field and describes `UNI\0` as classic AT&T System-V and `UNI\2` as Berkeley filesystem for System V. It also describes CrossDOS handler behavior and filesystem startup metadata.

The source is retained by the conversation/file system; this repository file is the provenance record and integration map.
