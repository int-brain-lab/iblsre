#!/bin/bash
RUN prefect work-pool create --type docker iblserver-docker-pool
RUN prefect worker start --pool iblserver-docker-pool
# NB: this needs to be run here: the relative path of this script needs to be the same as the relative path in the worker container
RUN python iblserver_prefect.py
