# Base containers

Those containers only need building when a big change of Python version / OS version / environment is necessary, and is rather infrequent.
The builds are meant to run on parede, and the images are pushed to the dockerhub international brain lab repository. 
The environments are non-trivial to solve, and it is not guaranteed that those dockerfiles will build in the future.


## ibllib

```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the IBLLIB base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/ibllib_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_ibllib_base
```

```shell
# push to docker hub
docker image push internationalbrainlab/ibllib_base:latest
```



## iblsorter
```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the IBLSORTER base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/iblsorter_base:latest  -f $DOCKER_BUILD_PATH/Dockerfile_iblsorter_base
```

```shell
# push to docker hub
docker image push internationalbrainlab/iblsorter_base:latest
```


## dlc
```shell
DOCKER_BUILD_PATH=~/Documents/PYTHON/iblsre/servers/containers
# builds the DLC base container
docker buildx build $DOCKER_BUILD_PATH --platform linux/amd64 --tag internationalbrainlab/dlc_base:latest -f $DOCKER_BUILD_PATH/Dockerfile_dlc_base
```

```shell
# push to docker hub
docker image push internationalbrainlab/dlc_base:latest
```