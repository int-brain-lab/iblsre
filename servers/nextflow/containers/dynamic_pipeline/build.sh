# usage: ./build.sh [--push]
PUSH=false

for arg in "$@"; do
    case "$arg" in
        --push) PUSH=true ;;
        *) echo "unknown argument: $arg (usage: ./build.sh [--push])" >&2; exit 1 ;;
    esac
done

# build the container
docker build -t internationalbrainlab/ibllib:dynamic_nextflow -f dynamic_pipeline.dockerfile .

# push only if asked for, requires an authenticated docker
if [ "${PUSH}" = true ]; then
    docker push internationalbrainlab/ibllib:dynamic_nextflow
fi
