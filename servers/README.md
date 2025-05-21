# On-call cheat-sheet

This is a collection of how-to guides for on-call operations on the IBL servers. 
- For a general description of the architecture, see the [explanations](./docs/architecture.md)
- For installation instructions see [the installation how-to](./docs/base_containers.md)
- For more information about the build of base docker images, see [base_containers.md](./docs/base_containers.md)


## Access the web interface of a local server through mbox
In your `.ssh/config` set up port-forwarding and hop through mbox:
```shell
Host mbox
    HostName 18.171.16.87
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/mbox

Host mbox-steinmetz
    User ibladmin
    ProxyCommand ssh -q mbox nc localhost 6668
    LocalForward 4200 localhost:4200
```
Once you have successfully run a ssh command, go to [https://localhost:4200](https://localhost:4200)


## Start the Prefect server

TODO move from tmux to a service for the worker.
TODO reset all concurrency slots on a hard reboot

On the local server.
```shell
tmux new -s prefect
iblcripts
cd ~/Documents/PYTHON/iblsre/servers/containers
python iblserver_prefect.py --scratch_directory /mnt/h0
prefect worker start --pool iblserver-docker-pool
```

## Update the code versions - create a canary

To update the codebase for one of the deployments or put one of the deployments on a canary, you have to build the top layer image using the `ibllib_branch` argument on the corresponding image.

```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the DLC container
docker buildx build $DOCKER_BUILD_PATH --pull --platform linux/amd64 --tag internationalbrainlab/dlc:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc --no-cache

# builds the IBLLIB container
docker buildx build $DOCKER_BUILD_PATH --pull --platform linux/amd64 --tag internationalbrainlab/ibllib:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib --no-cache --build-arg ibllib_branch=prefect

# builds the IBLSORTER container
docker buildx build $DOCKER_BUILD_PATH --pull --platform linux/amd64 --tag internationalbrainlab/iblsorter:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter --no-cache --build-arg ibllib_branch=prefect

# builds the PREFECT container
docker buildx build $DOCKER_BUILD_PATH --pull --platform linux/amd64 --tag internationalbrainlab/prefect:latest  -f $DOCKER_BUILD_PATH/Dockerfile_prefect --no-cache
```


## Acess a development environment for troubleshooting
TODO: should we put those commands available in the bashrc file ? 
### ibllib
```shell
# ibllib in interactive mode
docker run \
  -it \
  --rm \
  --name ibllib \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/home/ibladmin/.one \
  internationalbrainlab/ibllib
```

### iblsorter
```shell
SCRATCH_DIR=/mnt/h1
# run  in interactive mode with the volumes mounted
docker run \
  -it \
  --rm \
  --name spikesorter \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/home/ibladmin/.one \
  -v $SCRATCH_DIR:/scratch \
  internationalbrainlab/iblsorter:latest
```

### dlc
```shell
# ibllib in interactive mode
docker run \
  -it \
  --rm \
  --name ibllib \
  -v /mnt/s0:/mnt/s0 \
  -v /home/$USER/.one:/home/ibladmin/.one \
  internationalbrainlab/dlc
```
