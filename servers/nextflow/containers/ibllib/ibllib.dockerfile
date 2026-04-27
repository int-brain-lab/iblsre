FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/home/ubuntu/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# make sure all files in the home folder are owned by user ubuntu
WORKDIR /home/ubuntu

# system packages installable via apt
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ca-certificates \
    curl \
    git \
    nano \
    && rm -rf /var/lib/apt/lists/*

# UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# install packages via pip
RUN uv venv $VIRTUAL_ENV && \
    uv pip install --python $VIRTUAL_ENV ipython debugpy

# install via git, with specified branch
RUN uv pip install --python $VIRTUAL_ENV "git+https://github.com/int-brain-lab/ibllib.git@nextflow"

# the vscode debug functionality needs compatible versions between your local vscode install
# and the vscode-server installed in the docker image
# set the VSCode commit hash here (get it from Help → About in VSCode)
ARG VSCODE_COMMIT=10c8e557c8b9f9ed0a87f61f1c9a44bde731c409

# Install VSCode server and extensions
RUN curl -fsSL "https://update.code.visualstudio.com/commit:${VSCODE_COMMIT}/server-linux-x64/stable" \
    -o /tmp/vscode-server.tar.gz && \
    mkdir -p /home/ubuntu/.vscode-server/bin/${VSCODE_COMMIT} && \
    tar -xz --strip-components=1 -C /home/ubuntu/.vscode-server/bin/${VSCODE_COMMIT} \
    -f /tmp/vscode-server.tar.gz && \
    rm /tmp/vscode-server.tar.gz

RUN /home/ubuntu/.vscode-server/bin/${VSCODE_COMMIT}/bin/code-server \
    --install-extension ms-python.python \
    --install-extension ms-python.debugpy \
    --extensions-dir /home/ubuntu/.vscode-server/extensions

# port for debugging
EXPOSE 5678

# alyx credentials - multiple options
# simply moves over the current .one folder and all it's contents into the docker container
# COPY /home/$USER/.one /home/ubuntu/.one/

# alternatively, those are first copied, allows local modification
# COPY one_config /home/ubuntu/.one/

# or, can be specified as mount in docker run
# see run.sh