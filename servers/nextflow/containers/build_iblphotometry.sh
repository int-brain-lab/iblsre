# build the containers
# docker build -t ibllib:nextflow -f ibllib.dockerfile .

# build notes: the devcontainer.json contains some specific strings
# the dockerfile requires the commit hash of the local vscode installation
docker build -t iblphotometry:nextflow -f iblphotometry.dockerfile .
