FROM internationalbrainlab/ibllib:nextflow

# extra install
RUN uv pip install --python $VIRTUAL_ENV ibl-photometry

# make sure all files are owned by user ubuntu
# note - this can probably be solved by better user:group settings inside the container
RUN chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server

# scripts to run inside the container
# TODO move these to the base ibllib dockerfile
COPY photometry_sync.py /home/ubuntu/photometry_sync.py

# make all python files owned by ubuntu user
# (for debugging inside a container)
RUN chown  ubuntu:ubuntu /home/ubuntu/*.py
