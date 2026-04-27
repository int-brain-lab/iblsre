# TODO in cron: midnight builds

# build the containers
docker build -t internationalbrainlab/ibllib:dynamic_nextflow -f dynamic_pipeline.dockerfile .
docker push internationalbrainlab/ibllib:dynamic_nextflow