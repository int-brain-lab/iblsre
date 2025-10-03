#!/bin/bash
set -e

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Build Alyx Docker containers"
  echo ""
  echo "Options:"
  echo "  --top-only    Build only the top layer container"
  echo "  -h, --help    Display this help message"
  exit 1
}

# Parse command line arguments
TOP_ONLY=false
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --top-only) TOP_ONLY=true ;;
    -h|--help) usage ;;
    *) echo "Unknown parameter: $1"; usage ;;
  esac
  shift
done

# Build base container if not top-only
if [ "$TOP_ONLY" = false ]; then
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
  --build-arg alyx_branch=deploy \
  --no-cache
