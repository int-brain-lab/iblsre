# TODO in cron: midnight builds

# which ibllib branch gets installed into the image, override by setting DOCKER_IBLLIB_BRANCH
IBLLIB_BRANCH="${DOCKER_IBLLIB_BRANCH:-develop}"
echo "building ibllib container from branch: ${IBLLIB_BRANCH}"

# build the containers
docker build -t internationalbrainlab/ibllib:nextflow \
    --build-arg IBLLIB_BRANCH="${IBLLIB_BRANCH}" \
    -f ibllib.dockerfile .

# and push
docker push internationalbrainlab/ibllib:nextflow
