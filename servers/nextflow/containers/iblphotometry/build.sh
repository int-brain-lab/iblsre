#!/usr/bin/env bash
# usage: ./build.sh [branch] [--push]
# the branch of ibl-photometry to install, if empty, install from pypi
IBLPHOTOMETRY_BRANCH=""
PUSH=false

for arg in "$@"; do
    case "$arg" in
        --push) PUSH=true ;;
        -*) echo "unknown option: $arg (usage: ./build.sh [branch] [--push])" >&2; exit 1 ;;
        *) IBLPHOTOMETRY_BRANCH="$arg" ;;
    esac
done

if [ -z "${IBLPHOTOMETRY_BRANCH}" ]; then
    echo "building iblphotometry container with ibl-photometry from pypi"
else
    echo "building iblphotometry container with ibl-photometry from branch: ${IBLPHOTOMETRY_BRANCH}"
fi

# build the container
docker build -t internationalbrainlab/iblphotometry:nextflow \
    --build-arg IBLPHOTOMETRY_BRANCH="${IBLPHOTOMETRY_BRANCH}" \
    -f iblphotometry.dockerfile .

# push only if asked for, requires an authenticated docker
if [ "${PUSH}" = true ]; then
    docker push internationalbrainlab/iblphotometry:nextflow
fi
