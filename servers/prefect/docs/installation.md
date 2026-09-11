# Steps to install a machine as an IBL server

The playbook are targeted for Ubuntu family machines: Ubuntu and Mint. They may work or not on Debian OS.

TODO: move the documentation to build servers herem the full suite of documents is [here](https://docs.google.com/document/d/1NYVlVD8OkwRYUaPeHo3ZFPuwpv_E5zgUVjLsV0V5Ko4/edit?tab=t.0)
- install the Nvidia driver: we require support for CUDA 12, so the minimum driver is 530.
- install python (using uv ? )
- install RAID and create necessary folders
- install Globus
- what is the github policy ? Should a dev put a key in each server or we clone in http ? 


## Install Ansible

```shell
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

Clone the IBL sre repository 
```shell
mkdir -p ~/Documents/PYTHON
cd ~/Documents/PYTHON
git clone https://github.com/int-brain-lab/iblsre.git
```

## Install Docker with Support for Nvidia

```shell
cd ~/Documents/PYTHON/iblsre/servers/ansible
ansible-playbook docker-nvidia-container-setup.yaml --ask-become-pass
```
And then logout and login again.


## Install the Prefect pipeline (only once)
Pre-requisistes
TODO CRITICAL: install prefect and **configure concurrency** as an ansible workflow
TODO: recover docker logs in prefect 
TODO: add containers for suite2p, litpose
TODO: install prefect in ibllib environment. Should this be a separate env ? 
Big todo: try using dask runner to exploit multi-processing https://docs.prefect.io/integrations/prefect-dask


```shell
sudo systemctl stop ibl_large_jobs
sudo systemctl stop ibl_other_jobs
sudo systemctl disable ibl_large_jobs
sudo systemctl disable ibl_other_jobs
# also remove service files ? 
```
This only needs to happen once, has docker compose will restart after each reboot

```shell
# first start the dockerized prefect server
mkdir /mnt/s0/logs
cd ~/Documents/PYTHON/iblsre/servers
docker compose up -d
# then create the workpool locally
iblscripts
prefect work-pool create --type docker iblserver-docker-pool
prefect concurrency-limit  create gpu 1
prefect concurrency-limit  create large_jobs 3
prefect concurrency-limit  create small_jobs 6
```