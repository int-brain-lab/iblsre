# run the container mounting the .one directory for correct auth

# note the priviledged flag is only necessary on my local machine as I am mounting via sshfs

# takes care of the files being owned by root:root issue
USER_GROUP="-u $(id -u):$(id -g)"

# mounts the data drive
DATA_MOUNT="-v /mnt/s0/:/mnt/s0"

# for taking care of the one authentification
# potential pitfall here: cache folder might not be mounted
ONE_CONFIG_MOUNT="-v /home/$USER/.one:/home/ubuntu/.one"

docker run \
    -it \
    -p 5678:5678 \
    $USER_GROUP \
    $DATA_MOUNT \
    $ONE_CONFIG_MOUNT \
    internationalbrainlab/behavior:nextflow /bin/bash
