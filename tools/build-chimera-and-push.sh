#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPOSITORY="${DOCKERHUB_REPOSITORY:-amerhwitat/chimeraiios}"
TAG="${DOCKER_TAG:-latest}"

bash "$ROOT/build-chimera-iso.sh" "$@"

if [[ "${CHIMERA_PUSH:-1}" != 1 ]]; then
  printf '[INFO] Docker publication disabled (CHIMERA_PUSH=%s)\n' "${CHIMERA_PUSH:-1}"
  exit 0
fi

command -v docker >/dev/null 2>&1 || { echo '[ERROR] docker is required for publication' >&2; exit 2; }
[[ -n "${DOCKER_USERNAME:-}" && -n "${DOCKER_PASSWORD:-}" ]] || {
  echo '[ERROR] DOCKER_USERNAME and DOCKER_PASSWORD are required for Docker Hub publication' >&2
  exit 2
}
printf '%s' "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin
LOCAL_IMAGE="chimera2os-comprehensive:${TAG}"
docker image inspect "$LOCAL_IMAGE" >/dev/null

docker tag "$LOCAL_IMAGE" "$REPOSITORY:${TAG}"
docker tag "$LOCAL_IMAGE" "$REPOSITORY:latest"
docker tag "$LOCAL_IMAGE" "$REPOSITORY:$(git -C "$ROOT" rev-parse --short HEAD)"
docker push "$REPOSITORY:${TAG}"
[[ "$TAG" == latest ]] || docker push "$REPOSITORY:latest"
docker push "$REPOSITORY:$(git -C "$ROOT" rev-parse --short HEAD)"
printf '[SUCCESS] Docker Hub publication complete: %s\n' "$REPOSITORY"
