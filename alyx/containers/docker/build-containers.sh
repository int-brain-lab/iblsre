#!/bin/bash
set -e

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Build Alyx Docker containers"
  echo ""
  echo "Options:"
  echo "  --base        Build the base layer container as well"
  echo "  -h, --help    Display this help message"
  exit 1
}

# Parse command line arguments
BUILD_BASE=false
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --base) BUILD_BASE=true ;;
    -h|--help) usage ;;
    *) echo "Unknown parameter: $1"; usage ;;
  esac
  shift
done

# Build base container if --base is set
if [ "$BUILD_BASE" = true ]; then
  echo "Building base container..."
  docker buildx build . \
    --platform linux/amd64 \
    --tag internationalbrainlab/alyx_apache_base:latest \
    -f ./Dockerfile_base
fi

echo "Building head container..."
# builds the top layer
docker buildx build . \
  --platform linux/amd64 \
  --tag internationalbrainlab/alyx_apache:latest \
  -f ./Dockerfile \
  --no-cache
