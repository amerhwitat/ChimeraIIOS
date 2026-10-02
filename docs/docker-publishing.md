# Docker publishing

The comprehensive Chimera image is published to Docker Hub by `.github/workflows/chimera-dockerhub-publish.yml` on `main`, version tags, and manual dispatch.

Default repository:

`amerhwitat/chimeraiios`

Set the repository as the repository variable `DOCKERHUB_REPOSITORY` to override it.

Required GitHub Actions secrets:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD` (Docker Hub access token recommended)

The workflow publishes:

- `latest` on the default branch
- Git SHA tags
- release/version tags

No Docker credential is stored in source code or included in an ISO.
