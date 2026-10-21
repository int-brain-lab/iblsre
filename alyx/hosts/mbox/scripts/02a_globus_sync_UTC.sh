#!/bin/bash
# In-container: docker exec ibl_alyx_apache /bin/bash /home/scripts/02a_globus_sync_UTC.sh

echo "Start synchronisation for UTC time zone"

./manage.py files bulksync --lab=cortexlab
./manage.py files bulktransfer --lab=cortexlab

./manage.py files bulksync --lab=mainenlab
./manage.py files bulktransfer --lab=mainenlab

./manage.py files bulksync --lab=mrsicflogellab
./manage.py files bulktransfer --lab=mrsicflogellab

./manage.py files bulksync --lab=hoferlab
./manage.py files bulktransfer --lab=hoferlab

./manage.py files bulksync --lab=hausserlab
./manage.py files bulktransfer --lab=hausserlab

sleep 900

./manage.py files bulksync --lab=cortexlab
./manage.py files bulksync --lab=mainenlab
./manage.py files bulksync --lab=mrsicflogellab
./manage.py files bulksync --lab=hoferlab
./manage.py files bulksync --lab=hausserlab
