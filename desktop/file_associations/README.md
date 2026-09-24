# Aurora file properties and associations

Aurora uses one metadata model for files, directories, media, and applications. The model is compatible with the freedesktop MIME/application-association model while retaining Chimera-specific filesystem, security, media, and UI properties.

The registry separates what a file is (MIME/type metadata) from which application the user prefers (association/default application).

## Capabilities

- Complete file and directory property inspection.
- POSIX mode/owner/group plus ACL/xattr/security metadata when available.
- Symlink, mount-point, sparse-file and filesystem information.
- Optional SHA-256/SHA-512 content hashes.
- Recursive directory summaries without following symlink loops.
- Extension, MIME and content-type association resolution.
- Open-With and preferred-application handling.
- Audio/video/image metadata hooks.
- Thumbnail/icon/tag/rating/favorite fields for Aurora UI.
- Safe read-only inspection by default.

The association registry is data-driven so Aurora, media applications and video applications resolve the same file types and actions.
