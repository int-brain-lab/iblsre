# Ansible playbooks for servers installation

The playbook are targeted for Ubuntu family machines: Ubuntu and Mint. They may work or not on Debian OS.

## Install Ansible

```shell
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
``` 

Clone the IBL sre repository 
```shell
mkdir -p ~/Documents/PYTHON
cd ~/Documents/PYTHON
git clone git@github.com:int-brain-lab/iblsre.git
```


Pre-requisistes
TODO: install prefect and configure concurrency as an ansible workflow
TODO: recover docker logs in prefect 
TODO: procedure for canary and update
TODO: add containers for each env: ibllib, iblsorter, suite2p, litpose, dlc

```shell
mkdir /mnt/s0/logs
# TODO install python with uv
uv pip install prefect
prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect server start
prefect work-pool create --type docker iblserver-docker-pool
prefect worker start --pool iblserver-docker-pool
# TODO using ansible, install prefect and setup a service: https://docs.prefect.io/v3/deploy/daemonize-processes, 
# TODO using ansible, download all of the docker images needed for extraction

cd ~/Documents/PYTHON/iblsre/servers/containers
python iblserver_prefect.py   # NB: this needs to be run here: the relative path of this script needs to be the same as the relative path
prefect deployment run 'create-jobs/iblserver-create-jobs'
```


## Install Docker with Support for Nvidia

```shell
cd ~/Documents/PYTHON/iblsre/servers/ansible
ansible-playbook docker-nvidia-container-setup.yaml --ask-become-pass
```


## Build containers
The containers are setup with 2 images: a base image that contains all of the heavy lifting installation, and a second image that contains a few copy and git pull instructions to update the containers.
The idea is to be able to re-build and manipulate often only the small top layers, while the heavy layers are more stable.

```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the DLC containers
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/dlc_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc_base
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/dlc:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc --no-cache
# builds the IBLLIB containers
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/ibllib_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib_base
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/ibllib:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib --no-cache
# builds the IBLSORTER containers
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/iblsorter_base:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter_base
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/iblsorter:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter --no-cache
# At the end, deploy the flows to prefect and run
cd ~/Documents/PYTHON/iblsre/servers/containers
python iblserver_prefect.py   # NB: this needs to be run in the same directory as the script: the relative path of this script needs to be the same as the relative path
# at last, this is an example to run one of the deployments right away (by default the schedul)
prefect deployment run iblsorter-jobs/iblserver-iblsorter-jobs
```

```shell
docker image push internationalbrainlab/ibllib:latest
...


Run interactive mode with the volumes mounted
```shell

docker run \
  --it \
  --rm \
  --name spikesorter \
  --gpus 1 \
  -v /mnt/s1:/mnt/s1 \
  -v /home/$USER/.one:/root/.one \
  -v /mnt/h1:/scratch \
  internationalbrainlab/iblsorter:latest \
  python /root/Documents/PYTHON/ibl-sorter/examples/run_single_recording.py $BINFILE  /mnt/h1/iblsorter_integration --scratch_directory /scratch
```