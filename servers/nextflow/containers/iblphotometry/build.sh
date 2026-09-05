#!/usr/bin/env bash
# build notes: the devcontainer.json contains some specific strings
# the base ibllib dockerfile requires the commit hash of the local vscode installation

# usage: ./build.sh [branch]
# the branch of ibl-photometry to install, if empty, install from pypi
IBLPHOTOMETRY_BRANCH="${1:-}"

if [ -z "${IBLPHOTOMETRY_BRANCH}" ]; then
    echo "building iblphotometry container with ibl-photometry from pypi"
else
    echo "building iblphotometry container with ibl-photometry from branch: ${IBLPHOTOMETRY_BRANCH}"
fi

# build the container
docker build -t internationalbrainlab/iblphotometry:nextflow \
    --build-arg IBLPHOTOMETRY_BRANCH="${IBLPHOTOMETRY_BRANCH}" \
    -f iblphotometry.dockerfile .

# and push
docker push internationalbrainlab/iblphotometry:nextflow
