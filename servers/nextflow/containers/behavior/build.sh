#!/usr/bin/env bash
# usage: ./build.sh [--push]
# the behaviour container installs no package of its own, it inherits ibllib from its base image
# and only adds the entry scripts - build the ibllib container first to change the ibllib version
PUSH=false

for arg in "$@"; do
    case "$arg" in
        --push) PUSH=true ;;
        *) echo "unknown argument: $arg (usage: ./build.sh [--push])" >&2; exit 1 ;;
    esac
done

# build the container
docker build -t internationalbrainlab/behavior:nextflow \
    -f behavior.dockerfile .

# push only if asked for, requires an authenticated docker
if [ "${PUSH}" = true ]; then
    docker push internationalbrainlab/behavior:nextflow
fi
