FROM internationalbrainlab/ibllib:nextflow

# install ibl-photometry, either from pypi or, if a branch is given, from git
# set the branch with build.sh <branch>, or docker build --build-arg IBLPHOTOMETRY_BRANCH=<branch> ...
ARG IBLPHOTOMETRY_BRANCH=
RUN if [ -z "${IBLPHOTOMETRY_BRANCH}" ]; then \
    uv pip install --python $VIRTUAL_ENV ibl-photometry; \
    else \
    uv pip install --python $VIRTUAL_ENV "git+https://github.com/int-brain-lab/ibl-photometry.git@${IBLPHOTOMETRY_BRANCH}"; \
    fi

# make sure all files are owned by user ubuntu
# note - this can probably be solved by better user:group settings inside the container
RUN chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server

# scripts to run inside the container
# TODO move these to the base ibllib dockerfile
COPY photometry_sync.py /home/ubuntu/photometry_sync.py

# make all python files owned by ubuntu user
# (for debugging inside a container)
RUN chown  ubuntu:ubuntu /home/ubuntu/*.py
