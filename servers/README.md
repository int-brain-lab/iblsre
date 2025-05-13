# Ansible playbooks for servers installation

The playbook are targeted for Ubuntu family machines: Ubuntu and Mint. They may work or not on Debian OS.

TODO: move the documentation to build servers here
- install the Nvidia driver: we require support for CUDA 12, so the minimum driver is 530.
- install python (using uv ? )
- install RAID and create necessary folders
- install Globus
- what is the github policy ? Should a dev put a key in each server or we clone in http ? 


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
git clone https://github.com/int-brain-lab/iblsre.git
```

## Install Docker with Support for Nvidia

```shell
cd ~/Documents/PYTHON/iblsre/servers/ansible
ansible-playbook docker-nvidia-container-setup.yaml --ask-become-pass
```
And then logout and login again.

## Build containers
The containers are setup with 2 images: a base image that contains all of the heavy lifting installation, and a second image that contains a few copy and git pull instructions to update the containers.
The idea is to be able to re-build and manipulate often only the small top layers for python code updates and canaries, while the heavy layers containing environments are more stable.


### Build top layers
```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the DLC container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/dlc:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc --no-cache
# builds the IBLLIB container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/ibllib:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib --no-cache
# builds the IBLSORTER container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/iblsorter:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter --no-cache
# builds the PREFECT container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/prefect:latest  -f $DOCKER_BUILD_PATH/Dockerfile_prefect --no-cache

# At the end, deploy the flows to prefect and run
cd ~/Documents/PYTHON/iblsre/servers/containers
python iblserver_prefect.py   # NB: this needs to be run in the same directory as the script: the relative path of this script needs to be the same as the relative path in each one of the docker containers
# at last, this is an example to run one of the deployments right away (by default the scheduler)
prefect deployment run iblsorter-jobs/iblserver-iblsorter-jobs
```

### Build base images
Those steps are only necessary when a big change of Python version / OS version / environment is necessary, and is rather infrequent. The builds are meant to run on parede, and the images are pushed to the dockerhub international brain lab repository. 

```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the DLC base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/dlc_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc_base
# builds the IBLLIB base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/ibllib_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib_base
# builds the IBLSORTER base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/iblsorter_base:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter_base
```

```shell
# push all base containers to docker hub
docker image push internationalbrainlab/ibllib_base:latest
docker image push internationalbrainlab/iblsorter_base:latest
docker image push internationalbrainlab/dlc_base:latest
```

## Install the Pipeline (only once)
Pre-requisistes
TODO CRITICAL: install prefect and **configure concurrency** as an ansible workflow
TODO: recover docker logs in prefect 
TODO: procedure for canary and update
TODO: add containers for suite2p, litpose
TODO: install prefect in ibllib environment. Should this be a separate env ? 

Big todo: rebuild the containers with the 1000 user by default to mappings
https://stackoverflow.com/questions/72709443/how-to-have-consistent-ownership-of-mounted-volumes-in-docker

Big todo: try using dask runner to exploit multi-processing https://docs.prefect.io/integrations/prefect-dask


```shell
sudo systemctl stop ibl_large_jobs
sudo systemctl stop ibl_other_jobs
sudo systemctl disable ibl_large_jobs
sudo systemctl disable ibl_other_jobs
# also remove service files ? 
```
This only needs to happen once, has docker compose will restart after each reboot

```shell
# first start the dockerized prefect server
mkdir /mnt/s0/logs
cd ~/Documents/PYTHON/iblsre/servers
docker compose up -d
# then create the workpool locally
iblscripts
prefect work-pool create --type docker iblserver-docker-pool
```

## Start the Pipeline
TODO move from tmux to a service for the worker.
TODO reset all concurrency slots on a hard reboot
```shell
tmux new -s prefect
iblcripts
cd ~/Documents/PYTHON/iblsre/servers/containers
python iblserver_prefect.py --scratch_directory /mnt/h0
prefect worker start --pool iblserver-docker-pool
```

## Cheat sheet
#TODO: show how to have /mnt/s0 volumes in docker shell, maybe using compose, or by adding the options to the docker run call
```shell
# ibllib in interactive mode
docker run \
  -it \
  --rm \
  --name ibllib \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/root/.one \
  internationalbrainlab/ibllib

# run  in interactive mode with the volumes mounted
docker run \
  -it \
  --rm \
  --name spikesorter \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/root/.one \
  -v /mnt/h1:/scratch \  # FIXME this is a parameter
  internationalbrainlab/iblsorter:latest
```
