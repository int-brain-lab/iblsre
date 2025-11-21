#!/bin/bash
set -e

usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Build Alyx Docker containers"
  echo ""
  echo "Options:"
  echo "  --base           Build the base layer container as well"
  echo "  --monitoring     Build the monitoring variant container"
  echo "  --all           Build all containers (base, standard, and monitoring)"
  echo "  -h, --help       Display this help message"
  exit 1
}

# Parse command line arguments
BUILD_BASE=false
BUILD_MONITORING=false
BUILD_ALL=false
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --base) BUILD_BASE=true ;;
    --monitoring) BUILD_MONITORING=true ;;
    --all) BUILD_ALL=true ;;
    -h|--help) usage ;;
    *) echo "Unknown parameter: $1"; usage ;;
  esac
  shift
done

# Handle --all flag
if [ "$BUILD_ALL" = true ]; then
  BUILD_BASE=true
  BUILD_MONITORING=true
fi

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
  --build-arg alyx_branch=deploy \
  --no-cache

# Build monitoring container if --monitoring or --all is set
if [ "$BUILD_MONITORING" = true ]; then
  echo "Building monitoring container..."
  docker buildx build . \
    --platform linux/amd64 \
    --tag internationalbrainlab/alyx_apache_monitoring:latest \
    -f ./Dockerfile_monitoring \
    --build-arg alyx_branch=deploy \
    --no-cache
fi
