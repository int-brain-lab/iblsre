#!/usr/bin/env bash
# the behaviour container installs no package of its own, it inherits ibllib from its base image
# and only adds the entry scripts - build the ibllib container first to change the ibllib version

# build the container
docker build -t internationalbrainlab/behavior:nextflow \
    -f behavior.dockerfile .
