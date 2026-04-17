FROM ibllib:nextflow

# extra install
RUN uv pip install --python $VIRTUAL_ENV ibl-photometry

# make sure all files are owned by user ubuntu
# note - this can probably be solved by better user:group settings inside the container
RUN chown -R ubuntu:ubuntu /home/ubuntu/.vscode-server

# scripts to run inside the container
COPY run_single_alyx_task.py /home/ubuntu/run_single_alyx_task.py
COPY create_alyx_tasks.py /home/ubuntu/create_alyx_tasks.py