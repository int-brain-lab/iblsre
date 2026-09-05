#!/usr/bin/env bash
# TODO in cron: midnight builds

# usage: ./build.sh [branch]
# the branch of ibllib to install, if empty, install from pypi
IBLLIB_BRANCH="${1:-}"

if [ -z "${IBLLIB_BRANCH}" ]; then
    echo "building ibllib container with ibllib from pypi"
else
    echo "building ibllib container with ibllib from branch: ${IBLLIB_BRANCH}"
fi

# build the container
docker build -t internationalbrainlab/ibllib:nextflow \
    --build-arg IBLLIB_BRANCH="${IBLLIB_BRANCH}" \
    -f ibllib.dockerfile .

# and push
docker push internationalbrainlab/ibllib:nextflow
