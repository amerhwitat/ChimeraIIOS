#!/bin/bash
# =============================================================================
# COMPREHENSIVE CHIMERA II OS BUILD SCRIPT
# =============================================================================
# Builds the complete Chimera II OS Docker image with all integrated repos
# Author: Amer Abdullah Suleiman Hwitat
# Contact: amer.hwitat@proton.me
# =============================================================================

set -e

IMAGE_NAME="${1:-chimera2os-comprehensive}"
IMAGE_TAG="${2:-latest}"
DOCKERFILE="${3:-Dockerfile.comprehensive}"
BUILD_CONTEXT="${4:-.}"

echo "=================================================================="
echo "CHIMERA II OS - COMPREHENSIVE BUILD"
echo "created by Amer Abdullah Suleiman Hwitat - عامر الحويطات"
echo "Amman 11814/Jordan | contact: amer.hwitat@proton.me"
echo "=================================================================="
echo ""
echo "[INFO] Build Configuration:"
echo "  Image Name: $IMAGE_NAME"
echo "  Image Tag: $IMAGE_TAG"
echo "  Dockerfile: $DOCKERFILE"
echo "  Build Context: $BUILD_CONTEXT"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "[ERROR] Docker daemon is not running. Please start Docker."
    exit 1
fi

echo "[STEP 1] Building Docker image..."
echo "  This may take 30-45 minutes depending on your system..."
echo ""

docker build \
    -f "$BUILD_CONTEXT/$DOCKERFILE" \
    -t "$IMAGE_NAME:$IMAGE_TAG" \
    -t "$IMAGE_NAME:latest" \
    --progress=plain \
    "$BUILD_CONTEXT"

BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Build completed!"
    echo ""
    echo "[STEP 2] Image Information:"
    docker images "$IMAGE_NAME"
    echo ""
    echo "[STEP 3] To run the container:"
    echo "  docker run -it --rm $IMAGE_NAME:$IMAGE_TAG"
    echo ""
    echo "[STEP 4] With volume mounts:"
    echo "  docker run -it --rm -v /path/to/workspace:/workspace $IMAGE_NAME:$IMAGE_TAG"
    echo ""
    echo "[STEP 5] To push to registry:"
    echo "  docker tag $IMAGE_NAME:$IMAGE_TAG your-registry/$IMAGE_NAME:$IMAGE_TAG"
    echo "  docker push your-registry/$IMAGE_NAME:$IMAGE_TAG"
    echo ""
else
    echo ""
    echo "[ERROR] Build failed with exit code $BUILD_EXIT_CODE"
    exit 1
fi
