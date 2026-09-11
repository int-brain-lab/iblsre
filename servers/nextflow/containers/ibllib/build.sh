#!/usr/bin/env bash
# usage: ./build.sh [branch] [--push]
# the branch of ibllib to install, if empty, install from pypi
IBLLIB_BRANCH=""
PUSH=false

for arg in "$@"; do
    case "$arg" in
        --push) PUSH=true ;;
        -*) echo "unknown option: $arg (usage: ./build.sh [branch] [--push])" >&2; exit 1 ;;
        *) IBLLIB_BRANCH="$arg" ;;
    esac
done

if [ -z "${IBLLIB_BRANCH}" ]; then
    echo "building ibllib container with ibllib from pypi"
else
    echo "building ibllib container with ibllib from branch: ${IBLLIB_BRANCH}"
fi

# build the container
docker build -t internationalbrainlab/ibllib:nextflow \
    --build-arg IBLLIB_BRANCH="${IBLLIB_BRANCH}" \
    -f ibllib.dockerfile .

# push only if asked for, requires an authenticated docker
if [ "${PUSH}" = true ]; then
    docker push internationalbrainlab/ibllib:nextflow
fi
