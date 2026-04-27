# TODO in cron: midnight builds

# build the containers
docker build -t internationalbrainlab/ibllib:nextflow -f ibllib.dockerfile .

# and push
docker push internationalbrainlab/ibllib:nextflow