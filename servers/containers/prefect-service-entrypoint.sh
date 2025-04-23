#!/bin/bash
prefect server start
prefect work-pool create --type docker iblserver-docker-pool
prefect worker start --pool iblserver-docker-pool
# NB: this needs to be run here: the relative path of this script needs to be the same as the relative path in the worker container
python iblserver_prefect.py   

prefect deployment run 'create-jobs/iblserver-create-jobs'
