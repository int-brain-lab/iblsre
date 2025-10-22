#!/bin/bash
set -e

DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
CUDA_MAJOR_VERSION=11
IBLSORTER_VERSION=1.12
IBLLIB_BRANCH=prefect
SCRATCH_DIR=/home/$USER/scratch

# Load environment variables from .env file if it exists
if [ -f "$(dirname "$0")/.env" ]; then
  set -a # automatically export all variables
  source "$(dirname "$0")/.env"
  set +a # stop automatically exporting
fi

# build the base version of the image (this is quite long)
docker buildx build $DOCKER_BUILD_PATH \
  --platform linux/amd64 \
  --tag internationalbrainlab/iblsorter_base:cuda${CUDA_MAJOR_VERSION} \
  --build-arg CUDA_MAJOR_VERSION=${CUDA_MAJOR_VERSION} \
  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter_base

# build the head version of the container
docker buildx build $DOCKER_BUILD_PATH \
	--platform linux/amd64 \
	--tag internationalbrainlab/iblsorter:${IBLSORTER_VERSION} \
	--tag internationalbrainlab/iblsorter:latest \
  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter \
  --no-cache \
  --build-arg ibllib_branch=${IBLLIB_BRANCH} \
  --build-arg CUDA_MAJOR_VERSION=${CUDA_MAJOR_VERSION}


docker run \
  -it \
  --rm \
  --name spikesorter \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/home/ibladmin/.one \
  -v ${SCRATCH_DIR}:/scratch internationalbrainlab/iblsorter:${IBLSORTER_VERSION} \
  /bin/bash iblsorter-test
